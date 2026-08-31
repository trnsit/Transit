from datetime import datetime
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.scans.models import Scan, ScanFinding
from app.modules.repositories.models import Repository

class ScanStore:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, scan_id: UUID, user_id: UUID) -> Scan | None:
        # Securely fetch the scan matching user_id through Repository relationship
        result = await self.session.execute(
            select(Scan)
            .join(Scan.repository)
            .options(selectinload(Scan.findings))
            .where(
                Scan.id == scan_id,
                Repository.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def list_by_repository(self, repository_id: UUID, user_id: UUID) -> list[Scan]:
        # List scans for a repository that belongs to the user
        result = await self.session.execute(
            select(Scan)
            .join(Scan.repository)
            .options(selectinload(Scan.findings))
            .where(
                Scan.repository_id == repository_id,
                Repository.user_id == user_id
            )
            .order_by(Scan.created_at.desc())
        )
        return list(result.scalars().all())

    async def create(self, repository_id: UUID) -> Scan:
        # Create new scan entry with 'pending' status
        scan = Scan(
            repository_id=repository_id,
            status='pending'
        )
        self.session.add(scan)
        await self.session.commit()
        await self.session.refresh(scan)
        return scan

    async def update_status(self, scan_id: UUID, status: str, completed_at: datetime | None = None) -> Scan | None:
        # Update scan status internally (called by the scanner service)
        result = await self.session.execute(
            select(Scan).where(Scan.id == scan_id)
        )
        scan = result.scalar_one_or_none()
        if not scan:
            return None
            
        scan.status = status
        if completed_at:
            scan.completed_at = completed_at
            
        await self.session.commit()
        await self.session.refresh(scan)
        return scan

    async def save_findings(self, scan_id: UUID, findings_data: list[dict]) -> list[ScanFinding]:
        # Bulk insert findings for a completed scan
        findings = [
            ScanFinding(
                scan_id=scan_id,
                file_path=item["file"],
                line_number=item["line_number"],
                category=item["category"],
                algorithm=item["algorithm"],
                line_content=item["line_content"],
                # Add these three lines to store agent outputs
                is_false_positive=item.get("is_false_positive", False),
                agent_explanation=item.get("agent_explanation"),
                suggested_explanation=item.get("suggested_explanation")
            )
            for item in findings_data
        ]
        self.session.add_all(findings)
        await self.session.commit()
        return findings
