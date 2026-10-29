import time
from typing import List, Dict, Any, Optional, Tuple
from ortools.sat.python import cp_model
from ..schemas import ProblemData, ValidationData, SolveResponse, ValidateResponse, Proposal, Assignment, Violation, ConstraintKind
import logging
import uuid
from datetime import date, datetime

logger = logging.getLogger(__name__)

class SolverService:
    """Service for solving scheduling problems using OR-Tools CP-SAT."""
    
    def __init__(self, num_proposals: int = 5, time_limit_seconds: float = 30.0):
        self.num_proposals = num_proposals
        self.time_limit_seconds = time_limit_seconds
    
    async def solve(self, problem_data: ProblemData) -> SolveResponse:
        """Solve a scheduling problem and return multiple proposals."""
        start_time = time.time()
        
        try:
            logger.info(f"Starting to solve problem for period: {problem_data.period_id}")
            
            # Convert problem data to internal format
            members = {m.id: m for m in problem_data.members}
            shift_slots = problem_data.shift_slots
            constraints = problem_data.constraints
            
            # Create the CP-SAT model
            model = cp_model.CpModel()
            
            # Create variables and constraints
            assignments, hard_constraints, soft_constraints = self._create_model(
                model, members, shift_slots, constraints
            )
            
            # Solve for multiple proposals
            proposals = []
            for i in range(self.num_proposals):
                logger.info(f"Generating proposal {i + 1}/{self.num_proposals}")
                
                # Create a copy of the model for each proposal
                proposal_model = cp_model.CpModel()
                proposal_assignments, proposal_hard, proposal_soft = self._create_model(
                    proposal_model, members, shift_slots, constraints
                )
                
                # Add constraint to make this proposal different from previous ones
                if i > 0:
                    self._add_diversity_constraint(
                        proposal_model, proposal_assignments, 
                        [p.assignments for p in proposals], members
                    )
                
                # Solve the model
                solver = cp_model.CpSolver()
                solver.parameters.max_time_in_seconds = self.time_limit_seconds / self.num_proposals
                status = solver.Solve(proposal_model)
                
                if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
                    proposal = self._extract_proposal(
                        solver, proposal_assignments, members, shift_slots, 
                        problem_data.period_id, constraints
                    )
                    proposals.append(proposal)
                    logger.info(f"Proposal {i + 1} generated with penalty: {proposal.soft_penalty_total}")
                else:
                    logger.warning(f"Proposal {i + 1} not feasible")
                    break
            
            # Sort proposals by quality (lower penalty is better)
            proposals.sort(key=lambda p: (p.hard_violation_count, p.soft_penalty_total))
            
            # Limit to requested number of proposals
            proposals = proposals[:self.num_proposals]
            
            generation_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            logger.info(f"Generated {len(proposals)} proposals in {generation_time:.2f}ms")
            
            return SolveResponse(
                period_id=problem_data.period_id,
                proposals=proposals,
                generation_time_ms=generation_time,
                num_proposals=len(proposals)
            )
        
        except Exception as e:
            logger.error(f"Solve failed: {e}")
            raise
    
    async def validate(self, validation_data: ValidationData) -> ValidateResponse:
        """Validate a roster against constraints."""
        try:
            logger.info(f"Validating proposal: {validation_data.proposal_id}")
            
            # Convert validation data
            assignments = validation_data.assignments
            constraints = validation_data.constraints
            
            # Check hard constraints
            hard_violations = []
            soft_violations = []
            
            for constraint in constraints:
                violations = self._check_constraint_violation(
                    constraint, assignments
                )
                if violations:
                    if constraint.get("hard", False):
                        hard_violations.extend(violations)
                    else:
                        soft_violations.extend(violations)
            
            all_violations = hard_violations + soft_violations
            
            # Calculate totals
            hard_count = len(hard_violations)
            soft_penalty = sum(v.get("penalty", 0) for v in soft_violations)
            
            is_valid = hard_count == 0
            
            logger.info(f"Validation: {hard_count} hard violations, {soft_penalty} soft penalty")
            
            return ValidateResponse(
                proposal_id=validation_data.proposal_id,
                valid=is_valid,
                hard_violation_count=hard_count,
                soft_penalty_total=soft_penalty,
                violations=all_violations,
                pass=is_valid
            )
        
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            raise
    
    def _create_model(
        self, 
        model: cp_model.CpModel, 
        members: Dict[str, Any], 
        shift_slots: List[Any],
        constraints: List[Any]
    ) -> Tuple[Dict, List, List]:
        """Create the CP-SAT model with variables and constraints."""
        assignments = {}  # (date, shift_type_id, user_id) -> BoolVar
        hard_constraints = []
        soft_constraints = []
        
        # Create assignment variables
        for slot in shift_slots:
            date_val = slot.date
            shift_type_id = slot.shift_type_id
            for member_id in members:
                key = (date_val, shift_type_id, member_id)
                assignments[key] = model.NewBoolVar(f"assign_{date_val}_{shift_type_id}_{member_id}")
        
        # Add staffing constraints (min/max staff per shift)
        for slot in shift_slots:
            date_val = slot.date
            shift_type_id = slot.shift_type_id
            
            # Get all assignments for this shift slot
            slot_assignments = [
                assignments[(date_val, shift_type_id, member_id)]
                for member_id in members
            ]
            
            # Minimum staff constraint
            model.Add(sum(slot_assignments) >= slot.min_staff)
            
            # Maximum staff constraint
            model.Add(sum(slot_assignments) <= slot.max_staff)
        
        # Add member constraints
        for constraint in constraints:
            user_id = constraint.user_id
            kind = constraint.kind
            start_date = constraint.start_date
            end_date = constraint.end_date
            shift_type_id = constraint.shift_type_id
            hard = constraint.hard
            penalty = constraint.penalty
            
            if kind in [ConstraintKind.VACATION, ConstraintKind.UNAVAILABLE]:
                # Member cannot work on these dates
                for slot in shift_slots:
                    if start_date <= slot.date <= end_date:
                        if shift_type_id is None or slot.shift_type_id == shift_type_id:
                            key = (slot.date, slot.shift_type_id, user_id)
                            if key in assignments:
                                if hard:
                                    model.Add(assignments[key] == 0)
                                    hard_constraints.append(key)
                                else:
                                    # Soft constraint with penalty
                                    penalty_var = model.NewIntVar(0, penalty, f"penalty_{constraint.id}")
                                    model.Add(penalty_var == penalty * assignments[key])
                                    model.Minimize(sum(soft_constraints) + penalty_var)
                                    soft_constraints.append(penalty_var)
            
            elif kind == ConstraintKind.PREFERENCE_AVOID:
                # Member prefers not to work on these dates/shifts
                for slot in shift_slots:
                    if start_date <= slot.date <= end_date:
                        if shift_type_id is None or slot.shift_type_id == shift_type_id:
                            key = (slot.date, slot.shift_type_id, user_id)
                            if key in assignments:
                                penalty_var = model.NewIntVar(0, penalty, f"penalty_{constraint.id}")
                                model.Add(penalty_var == penalty * assignments[key])
                                model.Minimize(sum(soft_constraints) + penalty_var)
                                soft_constraints.append(penalty_var)
            
            elif kind == ConstraintKind.PREFERENCE_WANT:
                # Member prefers to work on these dates/shifts
                for slot in shift_slots:
                    if start_date <= slot.date <= end_date:
                        if shift_type_id is None or slot.shift_type_id == shift_type_id:
                            key = (slot.date, slot.shift_type_id, user_id)
                            if key in assignments:
                                # Penalty for NOT assigning
                                penalty_var = model.NewIntVar(0, penalty, f"penalty_{constraint.id}")
                                model.Add(penalty_var == penalty * (1 - assignments[key]))
                                model.Minimize(sum(soft_constraints) + penalty_var)
                                soft_constraints.append(penalty_var)
        
        # Add objective: minimize soft constraint violations
        if soft_constraints:
            model.Minimize(sum(soft_constraints))
        
        return assignments, hard_constraints, soft_constraints
    
    def _add_diversity_constraint(
        self, 
        model: cp_model.CpModel, 
        assignments: Dict, 
        previous_proposals: List[List[Assignment]],
        members: Dict[str, Any]
    ):
        """Add constraint to make this proposal different from previous ones."""
        # Simple diversity: at least one different assignment from each previous proposal
        for prev_proposal in previous_proposals:
            # Count how many assignments are different
            diff_count = model.NewIntVar(0, len(assignments), f"diff_count")
            
            # For each assignment variable, check if it's different from the previous proposal
            diff_vars = []
            for (date_val, shift_type_id, user_id), var in assignments.items():
                # Check if this assignment was made in the previous proposal
                was_assigned = any(
                    a.date == date_val and 
                    a.shift_type_id == shift_type_id and 
                    a.user_id == user_id
                    for a in prev_proposal
                )
                
                if was_assigned:
                    # If it was assigned before, penalize if we assign it again
                    diff_var = model.NewBoolVar(f"diff_{date_val}_{shift_type_id}_{user_id}")
                    model.Add(diff_var == (var == 0)).OnlyEnforceIf(var)
                    model.Add(diff_var == 1).OnlyEnforceIf(var.Not())
                    diff_vars.append(diff_var)
            
            if diff_vars:
                model.Add(sum(diff_vars) >= 1)
    
    def _extract_proposal(
        self,
        solver: cp_model.CpSolver,
        assignments: Dict,
        members: Dict[str, Any],
        shift_slots: List[Any],
        period_id: str,
        constraints: List[Any]
    ) -> Proposal:
        """Extract a proposal from the solver solution."""
        proposal_assignments = []
        violations = []
        soft_penalty = 0
        hard_violation_count = 0
        
        # Extract assignments
        for (date_val, shift_type_id, user_id), var in assignments.items():
            if solver.BooleanValue(var):
                proposal_assignments.append(Assignment(
                    date=date_val,
                    shift_type_id=shift_type_id,
                    user_id=user_id
                ))
        
        # Check constraints and count violations
        for constraint in constraints:
            constraint_violations = self._check_constraint_violation(
                constraint, proposal_assignments
            )
            
            for violation in constraint_violations:
                if constraint.hard:
                    hard_violation_count += 1
                else:
                    soft_penalty += violation.get("penalty", 0)
                
                violations.append(violation)
        
        # Generate proposal ID
        proposal_id = str(uuid.uuid4())
        
        return Proposal(
            id=proposal_id,
            period_id=period_id,
            assignments=proposal_assignments,
            violations=violations,
            soft_penalty_total=soft_penalty,
            hard_violation_count=hard_violation_count,
            status="candidate"
        )
    
    def _check_constraint_violation(
        self,
        constraint: Dict[str, Any],
        assignments: List[Assignment]
    ) -> List[Dict[str, Any]]:
        """Check if a constraint is violated by the given assignments."""
        violations = []
        user_id = constraint.user_id
        kind = constraint.kind
        start_date = constraint.start_date
        end_date = constraint.end_date
        shift_type_id = constraint.shift_type_id
        hard = constraint.hard
        penalty = constraint.penalty
        
        # Get assignments for this user
        user_assignments = [
            a for a in assignments 
            if a.user_id == user_id
        ]
        
        if kind in [ConstraintKind.VACATION, ConstraintKind.UNAVAILABLE]:
            # Check if user is assigned during their vacation/unavailable period
            for assignment in user_assignments:
                if start_date <= assignment.date <= end_date:
                    if shift_type_id is None or assignment.shift_type_id == shift_type_id:
                        violations.append(Violation(
                            constraint_id=constraint.id,
                            constraint_kind=kind,
                            hard=hard,
                            user_id=user_id,
                            date=assignment.date,
                            message=f"User {user_id} is assigned on {assignment.date} during {kind}",
                            penalty=penalty if not hard else 0
                        ))
        
        elif kind == ConstraintKind.PREFERENCE_AVOID:
            # Check if user is assigned when they prefer to avoid
            for assignment in user_assignments:
                if start_date <= assignment.date <= end_date:
                    if shift_type_id is None or assignment.shift_type_id == shift_type_id:
                        violations.append(Violation(
                            constraint_id=constraint.id,
                            constraint_kind=kind,
                            hard=hard,
                            user_id=user_id,
                            date=assignment.date,
                            message=f"User {user_id} prefers to avoid shift {assignment.shift_type_id} on {assignment.date}",
                            penalty=penalty
                        ))
        
        elif kind == ConstraintKind.PREFERENCE_WANT:
            # Check if user is NOT assigned when they prefer to work
            # Get all shift slots for the date range
            for slot in self._get_shift_slots_in_range(
                [s for s in self._get_all_shift_slots() if s.date >= start_date and s.date <= end_date],
                start_date, end_date
            ):
                if shift_type_id is None or slot.shift_type_id == shift_type_id:
                    # Check if user is assigned to this shift
                    is_assigned = any(
                        a.date == slot.date and a.shift_type_id == slot.shift_type_id and a.user_id == user_id
                        for a in user_assignments
                    )
                    
                    if not is_assigned:
                        violations.append(Violation(
                            constraint_id=constraint.id,
                            constraint_kind=kind,
                            hard=hard,
                            user_id=user_id,
                            date=slot.date,
                            message=f"User {user_id} prefers to work shift {slot.shift_type_id} on {slot.date}",
                            penalty=penalty
                        ))
        
        return violations
    
    def _get_shift_slots_in_range(
        self,
        shift_slots: List[Any],
        start_date: date,
        end_date: date
    ) -> List[Any]:
        """Get shift slots within a date range."""
        return [
            slot for slot in shift_slots
            if start_date <= slot.date <= end_date
        ]
    
    def _get_all_shift_slots(self) -> List[Any]:
        """Get all shift slots (placeholder)."""
        return []

# Global solver service instance
solver_service = SolverService()
