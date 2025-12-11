"""Reference Integrity Checker for Keyword Manager

K-file 내 참조 무결성을 검사합니다.
예: Part의 SECID가 실제 Section에 존재하는지, Element의 노드 ID가 실제 노드에 존재하는지 등
"""
from typing import Dict, List, Set, Any, Optional, TYPE_CHECKING
from dataclasses import dataclass, field
from enum import Enum

if TYPE_CHECKING:
    from gui.app_context import ParsedModelData


class SeverityLevel(Enum):
    """문제 심각도"""
    ERROR = "error"      # 심각한 오류 (모델 실행 불가능)
    WARNING = "warning"  # 경고 (실행은 가능하나 결과가 이상할 수 있음)
    INFO = "info"        # 정보성 메시지


@dataclass
class IntegrityIssue:
    """무결성 문제"""
    severity: SeverityLevel
    category: str
    item_id: Any
    field_name: str
    message: str
    referenced_category: str = ""
    referenced_id: Any = None

    def __str__(self) -> str:
        """문자열 표현"""
        return f"[{self.severity.value.upper()}] {self.category} {self.item_id}: {self.message}"


@dataclass
class IntegrityReport:
    """무결성 검사 보고서"""
    errors: List[IntegrityIssue] = field(default_factory=list)
    warnings: List[IntegrityIssue] = field(default_factory=list)
    infos: List[IntegrityIssue] = field(default_factory=list)

    def add_issue(self, issue: IntegrityIssue):
        """문제 추가"""
        if issue.severity == SeverityLevel.ERROR:
            self.errors.append(issue)
        elif issue.severity == SeverityLevel.WARNING:
            self.warnings.append(issue)
        else:
            self.infos.append(issue)

    @property
    def total_issues(self) -> int:
        """전체 문제 수"""
        return len(self.errors) + len(self.warnings) + len(self.infos)

    @property
    def has_errors(self) -> bool:
        """에러 존재 여부"""
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        """경고 존재 여부"""
        return len(self.warnings) > 0

    def get_all_issues(self) -> List[IntegrityIssue]:
        """모든 문제 반환 (심각도 순)"""
        return self.errors + self.warnings + self.infos

    def __str__(self) -> str:
        """문자열 표현"""
        lines = [
            "=" * 80,
            "  Integrity Check Report",
            "=" * 80,
            f"Errors:   {len(self.errors)}",
            f"Warnings: {len(self.warnings)}",
            f"Infos:    {len(self.infos)}",
            "=" * 80,
        ]

        if self.errors:
            lines.append("\nERRORS:")
            for issue in self.errors:
                lines.append(f"  {issue}")

        if self.warnings:
            lines.append("\nWARNINGS:")
            for issue in self.warnings:
                lines.append(f"  {issue}")

        if self.infos:
            lines.append("\nINFOS:")
            for issue in self.infos:
                lines.append(f"  {issue}")

        lines.append("=" * 80)
        return '\n'.join(lines)


class IntegrityChecker:
    """참조 무결성 검사기

    K-file 내의 모든 참조가 유효한지 검사합니다.
    """

    def __init__(self, model: 'ParsedModelData'):
        self._model = model

    def check_all(self) -> IntegrityReport:
        """전체 무결성 검사"""
        report = IntegrityReport()

        # ID 세트 구축
        node_ids = self._build_id_set('nodes', 'nid')
        part_ids = self._build_id_set('parts', 'pid')
        section_ids = self._build_id_set('sections', 'secid')
        material_ids = self._build_id_set('materials', 'mid')

        # 각 카테고리 검사
        self._check_elements(report, node_ids, part_ids)
        self._check_parts(report, section_ids, material_ids)
        self._check_duplicate_ids(report)
        self._check_node_coordinates(report)

        return report

    def _build_id_set(self, category: str, id_field: str) -> Set[int]:
        """ID 세트 구축"""
        ids = set()
        items = self._get_items(category)

        for item in items:
            item_id = getattr(item, id_field, None)
            if item_id is not None:
                try:
                    ids.add(int(item_id))
                except (ValueError, TypeError):
                    pass

        return ids

    def _get_items(self, category: str) -> List[Any]:
        """카테고리별 항목 조회"""
        if category == 'nodes':
            return self._model.nodes if self._model.nodes else []
        elif category == 'shell':
            return self._model.shells if self._model.shells else []
        elif category == 'solid':
            return self._model.solids if self._model.solids else []
        elif category == 'beam':
            return self._model.beams if self._model.beams else []
        elif category == 'parts':
            return self._model.parts if self._model.parts else []
        elif category == 'materials':
            return self._model.materials if self._model.materials else []
        elif category == 'sections':
            return self._model.sections if self._model.sections else []
        else:
            return []

    def _check_elements(self, report: IntegrityReport, node_ids: Set[int], part_ids: Set[int]):
        """요소 참조 검사"""
        # Shell elements
        for elem in self._get_items('shell'):
            eid = getattr(elem, 'eid', None)
            pid = getattr(elem, 'pid', None)
            nodes = getattr(elem, 'nodes', [])

            # PID 참조 검사
            if pid is not None and int(pid) not in part_ids:
                report.add_issue(IntegrityIssue(
                    severity=SeverityLevel.ERROR,
                    category='shell',
                    item_id=eid,
                    field_name='pid',
                    message=f"Shell {eid} references non-existent part PID={pid}",
                    referenced_category='parts',
                    referenced_id=pid
                ))

            # 노드 참조 검사
            for i, nid in enumerate(nodes):
                if nid != 0 and int(nid) not in node_ids:
                    report.add_issue(IntegrityIssue(
                        severity=SeverityLevel.ERROR,
                        category='shell',
                        item_id=eid,
                        field_name=f'node{i+1}',
                        message=f"Shell {eid} references non-existent node NID={nid}",
                        referenced_category='nodes',
                        referenced_id=nid
                    ))

        # Solid elements
        for elem in self._get_items('solid'):
            eid = getattr(elem, 'eid', None)
            pid = getattr(elem, 'pid', None)
            nodes = getattr(elem, 'nodes', [])

            if pid is not None and int(pid) not in part_ids:
                report.add_issue(IntegrityIssue(
                    severity=SeverityLevel.ERROR,
                    category='solid',
                    item_id=eid,
                    field_name='pid',
                    message=f"Solid {eid} references non-existent part PID={pid}",
                    referenced_category='parts',
                    referenced_id=pid
                ))

            for i, nid in enumerate(nodes):
                if nid != 0 and int(nid) not in node_ids:
                    report.add_issue(IntegrityIssue(
                        severity=SeverityLevel.ERROR,
                        category='solid',
                        item_id=eid,
                        field_name=f'node{i+1}',
                        message=f"Solid {eid} references non-existent node NID={nid}",
                        referenced_category='nodes',
                        referenced_id=nid
                    ))

    def _check_parts(self, report: IntegrityReport, section_ids: Set[int], material_ids: Set[int]):
        """파트 참조 검사"""
        for part in self._get_items('parts'):
            pid = getattr(part, 'pid', None)
            secid = getattr(part, 'secid', None)
            mid = getattr(part, 'mid', None)

            # SECID 참조 검사
            if secid is not None and secid != 0 and int(secid) not in section_ids:
                report.add_issue(IntegrityIssue(
                    severity=SeverityLevel.ERROR,
                    category='parts',
                    item_id=pid,
                    field_name='secid',
                    message=f"Part {pid} references non-existent section SECID={secid}",
                    referenced_category='sections',
                    referenced_id=secid
                ))

            # MID 참조 검사
            if mid is not None and mid != 0 and int(mid) not in material_ids:
                report.add_issue(IntegrityIssue(
                    severity=SeverityLevel.ERROR,
                    category='parts',
                    item_id=pid,
                    field_name='mid',
                    message=f"Part {pid} references non-existent material MID={mid}",
                    referenced_category='materials',
                    referenced_id=mid
                ))

    def _check_duplicate_ids(self, report: IntegrityReport):
        """중복 ID 검사"""
        self._check_category_duplicates(report, 'nodes', 'nid')
        self._check_category_duplicates(report, 'shell', 'eid')
        self._check_category_duplicates(report, 'solid', 'eid')
        self._check_category_duplicates(report, 'parts', 'pid')
        self._check_category_duplicates(report, 'materials', 'mid')
        self._check_category_duplicates(report, 'sections', 'secid')

    def _check_category_duplicates(self, report: IntegrityReport, category: str, id_field: str):
        """카테고리별 중복 ID 검사"""
        items = self._get_items(category)
        seen_ids = {}

        for item in items:
            item_id = getattr(item, id_field, None)
            if item_id is None:
                continue

            try:
                item_id = int(item_id)
            except (ValueError, TypeError):
                continue

            if item_id in seen_ids:
                report.add_issue(IntegrityIssue(
                    severity=SeverityLevel.ERROR,
                    category=category,
                    item_id=item_id,
                    field_name=id_field,
                    message=f"Duplicate {id_field.upper()}={item_id} in {category}"
                ))
            else:
                seen_ids[item_id] = item

    def _check_node_coordinates(self, report: IntegrityReport):
        """노드 좌표 검사"""
        for node in self._get_items('nodes'):
            nid = getattr(node, 'nid', None)
            x = getattr(node, 'x', 0.0)
            y = getattr(node, 'y', 0.0)
            z = getattr(node, 'z', 0.0)

            # 매우 큰 좌표값 경고
            max_coord = 1e10
            if abs(x) > max_coord or abs(y) > max_coord or abs(z) > max_coord:
                report.add_issue(IntegrityIssue(
                    severity=SeverityLevel.WARNING,
                    category='nodes',
                    item_id=nid,
                    field_name='coordinates',
                    message=f"Node {nid} has very large coordinates: ({x:.2e}, {y:.2e}, {z:.2e})"
                ))

            # NaN 검사
            try:
                if x != x or y != y or z != z:  # NaN check
                    report.add_issue(IntegrityIssue(
                        severity=SeverityLevel.ERROR,
                        category='nodes',
                        item_id=nid,
                        field_name='coordinates',
                        message=f"Node {nid} has NaN coordinates"
                    ))
            except:
                pass

    def check_category(self, category: str) -> IntegrityReport:
        """특정 카테고리만 검사"""
        report = IntegrityReport()

        if category == 'nodes':
            self._check_category_duplicates(report, 'nodes', 'nid')
            self._check_node_coordinates(report)

        elif category in ('shell', 'solid', 'beam'):
            node_ids = self._build_id_set('nodes', 'nid')
            part_ids = self._build_id_set('parts', 'pid')
            self._check_elements(report, node_ids, part_ids)

        elif category == 'parts':
            section_ids = self._build_id_set('sections', 'secid')
            material_ids = self._build_id_set('materials', 'mid')
            self._check_parts(report, section_ids, material_ids)
            self._check_category_duplicates(report, 'parts', 'pid')

        elif category == 'materials':
            self._check_category_duplicates(report, 'materials', 'mid')

        elif category == 'sections':
            self._check_category_duplicates(report, 'sections', 'secid')

        return report

    def check_item(self, category: str, item: Any) -> IntegrityReport:
        """특정 항목만 검사"""
        report = IntegrityReport()

        if category == 'nodes':
            nid = getattr(item, 'nid', None)
            # 중복 ID 검사
            node_ids = self._build_id_set('nodes', 'nid')
            if nid in node_ids:
                # 자기 자신을 제외하고 중복 확인
                count = sum(1 for n in self._get_items('nodes') if getattr(n, 'nid', None) == nid)
                if count > 1:
                    report.add_issue(IntegrityIssue(
                        severity=SeverityLevel.ERROR,
                        category='nodes',
                        item_id=nid,
                        field_name='nid',
                        message=f"Duplicate NID={nid}"
                    ))

        elif category in ('shell', 'solid'):
            eid = getattr(item, 'eid', None)
            pid = getattr(item, 'pid', None)
            nodes = getattr(item, 'nodes', [])

            node_ids = self._build_id_set('nodes', 'nid')
            part_ids = self._build_id_set('parts', 'pid')

            if pid is not None and int(pid) not in part_ids:
                report.add_issue(IntegrityIssue(
                    severity=SeverityLevel.ERROR,
                    category=category,
                    item_id=eid,
                    field_name='pid',
                    message=f"{category.capitalize()} {eid} references non-existent part PID={pid}",
                    referenced_category='parts',
                    referenced_id=pid
                ))

            for i, nid in enumerate(nodes):
                if nid != 0 and int(nid) not in node_ids:
                    report.add_issue(IntegrityIssue(
                        severity=SeverityLevel.ERROR,
                        category=category,
                        item_id=eid,
                        field_name=f'node{i+1}',
                        message=f"{category.capitalize()} {eid} references non-existent node NID={nid}",
                        referenced_category='nodes',
                        referenced_id=nid
                    ))

        elif category == 'parts':
            pid = getattr(item, 'pid', None)
            secid = getattr(item, 'secid', None)
            mid = getattr(item, 'mid', None)

            section_ids = self._build_id_set('sections', 'secid')
            material_ids = self._build_id_set('materials', 'mid')

            if secid is not None and secid != 0 and int(secid) not in section_ids:
                report.add_issue(IntegrityIssue(
                    severity=SeverityLevel.ERROR,
                    category='parts',
                    item_id=pid,
                    field_name='secid',
                    message=f"Part {pid} references non-existent section SECID={secid}",
                    referenced_category='sections',
                    referenced_id=secid
                ))

            if mid is not None and mid != 0 and int(mid) not in material_ids:
                report.add_issue(IntegrityIssue(
                    severity=SeverityLevel.ERROR,
                    category='parts',
                    item_id=pid,
                    field_name='mid',
                    message=f"Part {pid} references non-existent material MID={mid}",
                    referenced_category='materials',
                    referenced_id=mid
                ))

        return report
