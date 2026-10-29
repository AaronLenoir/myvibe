from typing import Optional, list, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_
from sqlalchemy.orm import joinedload
from sqlalchemy.dialects.postgresql import insert
from ..models.roster_proposal import RosterProposal, ProposalStatus
from ..models.assignment import Assignment
from ..models.violation import Violation
from ..models.schedule_period import SchedulePeriod
from ..schemas.roster_proposal import RosterProposalRead
from ..schemas.assignment import AssignmentRead, AssignmentCreate
from ..schemas.violation import ViolationRead
from ..services.solver_service import solver_service
import uuid
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ProposalService:
    """Service for managing roster proposals."""
    
    def __init__(self):
        pass
    
    async def create_proposal(
        self,
        session: AsyncSession,
        period_id: uuid.UUID,
        assignments: list[AssignmentCreate],
        violations: list[dict],
        soft_penalty_total: int = 0,
        hard_violation_count: int = 0
    ) -> RosterProposalRead:
        """Create a new roster proposal."""
        proposal = RosterProposal(
            period_id=period_id,
            soft_penalty_total=soft_penalty_total,
            hard_violation_count=hard_violation_count,
            status=ProposalStatus.CANDIDATE
        )
        session.add(proposal)
        await session.commit()
        await session.refresh(proposal)
        
        # Add assignments
        for assignment in assignments:
            db_assignment = Assignment(
                proposal_id=proposal.id,
                **assignment.model_dump()
            )
            session.add(db_assignment)
        
        # Add violations
        for violation_data in violations:
            violation = Violation(
                proposal_id=proposal.id,
                **violation_data
            )
            session.add(violation)
        
        await session.commit()
        logger.info(f"Created proposal: {proposal.id} with {len(assignments)} assignments and {len(violations)} violations")
        
        return await self.get_proposal_with_details(session, proposal.id)
    
    async def get_proposal(self, session: AsyncSession, proposal_id: uuid.UUID) -> Optional[RosterProposalRead]:
        """Get a proposal by ID."""
        result = await session.execute(
            select(RosterProposal).where(RosterProposal.id == proposal_id)
        )
        proposal = result.scalar_one_or_none()
        if proposal:
            return RosterProposalRead.model_validate(proposal)
        return None
    
    async def get_proposals_by_period(self, session: AsyncSession, period_id: uuid.UUID) -> list[RosterProposalRead]:
        """Get all proposals for a schedule period."""
        result = await session.execute(
            select(RosterProposal).where(RosterProposal.period_id == period_id)
            .order_by(RosterProposal.soft_penalty_total.asc(), RosterProposal.hard_violation_count.asc())
        )
        proposals = result.scalars().all()
        return [RosterProposalRead.model_validate(p) for p in proposals]
    
    async def get_proposal_with_details(self, session: AsyncSession, proposal_id: uuid.UUID) -> Optional[RosterProposalRead]:
        """Get a proposal with all assignments and violations."""
        result = await session.execute(
            select(RosterProposal)
            .options(
                joinedload(RosterProposal.assignments),
                joinedload(RosterProposal.violations)
            )
            .where(RosterProposal.id == proposal_id)
        )
        proposal = result.scalar_one_or_none()
        if proposal:
            return RosterProposalRead.model_validate(proposal)
        return None
    
    async def get_selected_proposal(self, session: AsyncSession, period_id: uuid.UUID) -> Optional[RosterProposalRead]:
        """Get the selected proposal for a period."""
        result = await session.execute(
            select(RosterProposal).where(
                RosterProposal.period_id == period_id,
                RosterProposal.status == ProposalStatus.SELECTED
            )
        )
        proposal = result.scalar_one_or_none()
        if proposal:
            return RosterProposalRead.model_validate(proposal)
        return None
    
    async def select_proposal(self, session: AsyncSession, proposal_id: uuid.UUID) -> Optional[RosterProposalRead]:
        """Select a proposal as the chosen one for its period."""
        # First, deselect any existing selected proposal for the same period
        result = await session.execute(
            select(RosterProposal).where(RosterProposal.id == proposal_id)
        )
        proposal = result.scalar_one_or_none()
        
        if not proposal:
            return None
        
        # Deselect other proposals for the same period
        await session.execute(
            update(RosterProposal)
            .where(
                RosterProposal.period_id == proposal.period_id,
                RosterProposal.status == ProposalStatus.SELECTED
            )
            .values(status=ProposalStatus.CANDIDATE)
        )
        
        # Select the chosen proposal
        proposal.status = ProposalStatus.SELECTED
        await session.commit()
        logger.info(f"Selected proposal: {proposal_id}")
        
        return RosterProposalRead.model_validate(proposal)
    
    async def update_proposal_status(self, session: AsyncSession, proposal_id: uuid.UUID, status: ProposalStatus) -> Optional[RosterProposalRead]:
        """Update the status of a proposal."""
        result = await session.execute(
            update(RosterProposal)
            .where(RosterProposal.id == proposal_id)
            .values(status=status)
            .returning(RosterProposal)
        )
        proposal = result.scalar_one_or_none()
        if proposal:
            await session.commit()
            return RosterProposalRead.model_validate(proposal)
        return None
    
    async def delete_proposal(self, session: AsyncSession, proposal_id: uuid.UUID) -> bool:
        """Delete a proposal and all its assignments and violations."""
        result = await session.execute(
            delete(RosterProposal).where(RosterProposal.id == proposal_id)
        )
        if result.rowcount > 0:
            await session.commit()
            logger.info(f"Deleted proposal: {proposal_id}")
            return True
        return False
    
    async def delete_proposals_by_period(self, session: AsyncSession, period_id: uuid.UUID) -> int:
        """Delete all proposals for a period."""
        result = await session.execute(
            delete(RosterProposal).where(RosterProposal.period_id == period_id)
        )
        count = result.rowcount
        if count > 0:
            await session.commit()
            logger.info(f"Deleted {count} proposals for period: {period_id}")
        return count
    
    async def get_assignments_by_proposal(self, session: AsyncSession, proposal_id: uuid.UUID) -> list[AssignmentRead]:
        """Get all assignments for a proposal."""
        result = await session.execute(
            select(Assignment).where(Assignment.proposal_id == proposal_id)
        )
        assignments = result.scalars().all()
        return [AssignmentRead.model_validate(a) for a in assignments]
    
    async def get_assignments_by_user_and_proposal(self, session: AsyncSession, proposal_id: uuid.UUID, user_id: uuid.UUID) -> list[AssignmentRead]:
        """Get all assignments for a user in a proposal."""
        result = await session.execute(
            select(Assignment).where(
                Assignment.proposal_id == proposal_id,
                Assignment.user_id == user_id
            )
        )
        assignments = result.scalars().all()
        return [AssignmentRead.model_validate(a) for a in assignments]
    
    async def add_assignment(self, session: AsyncSession, assignment: AssignmentCreate) -> AssignmentRead:
        """Add an assignment to a proposal."""
        db_assignment = Assignment(**assignment.model_dump())
        session.add(db_assignment)
        await session.commit()
        await session.refresh(db_assignment)
        logger.info(f"Added assignment: {db_assignment.id}")
        return AssignmentRead.model_validate(db_assignment)
    
    async def remove_assignment(self, session: AsyncSession, assignment_id: uuid.UUID) -> bool:
        """Remove an assignment from a proposal."""
        result = await session.execute(
            delete(Assignment).where(Assignment.id == assignment_id)
        )
        if result.rowcount > 0:
            await session.commit()
            logger.info(f"Removed assignment: {assignment_id}")
            return True
        return False
    
    async def get_violations_by_proposal(self, session: AsyncSession, proposal_id: uuid.UUID) -> list[ViolationRead]:
        """Get all violations for a proposal."""
        result = await session.execute(
            select(Violation).where(Violation.proposal_id == proposal_id)
        )
        violations = result.scalars().all()
        return [ViolationRead.model_validate(v) for v in violations]
    
    async def generate_proposals_from_solver(
        self,
        session: AsyncSession,
        period_id: uuid.UUID,
        solver_response: dict
    ) -> list[RosterProposalRead]:
        """Create proposals from solver response."""
        proposals = []
        
        for proposal_data in solver_response.get("proposals", []):
            # Create assignments
            assignments = []
            for assignment_data in proposal_data.get("assignments", []):
                assignments.append(AssignmentCreate(
                    proposal_id=uuid.UUID(proposal_data.get("id", str(uuid.uuid4()))),
                    date=assignment_data.get("date"),
                    shift_type_id=assignment_data.get("shift_type_id"),
                    user_id=assignment_data.get("user_id")
                ))
            
            # Create violations
            violations = []
            for violation_data in proposal_data.get("violations", []):
                violations.append({
                    "constraint_kind": violation_data.get("constraint_kind"),
                    "hard": violation_data.get("hard", False),
                    "user_id": violation_data.get("user_id"),
                    "date": violation_data.get("date"),
                    "message": violation_data.get("message", ""),
                    "penalty": violation_data.get("penalty", 0)
                })
            
            proposal = await self.create_proposal(
                session=session,
                period_id=period_id,
                assignments=assignments,
                violations=violations,
                soft_penalty_total=proposal_data.get("soft_penalty_total", 0),
                hard_violation_count=proposal_data.get("hard_violation_count", 0)
            )
            proposals.append(proposal)
        
        return proposals

# Global proposal service instance
proposal_service = ProposalService()
