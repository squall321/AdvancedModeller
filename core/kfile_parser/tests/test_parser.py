"""K-file Parser 테스트"""
import os
import sys
from pathlib import Path

# 상위 폴더를 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_python_fallback():
    """Python 폴백 파서 테스트"""
    print("=== Python 폴백 파서 테스트 ===")

    from kfile_parser import KFileParser, is_cpp_available
    from kfile_parser.wrapper import SetType

    print(f"C++ 파서 사용 가능: {is_cpp_available()}")

    parser = KFileParser()
    print(f"현재 백엔드: {'C++' if parser.using_cpp else 'Python'}")

    # sample.k 파일 경로
    sample_path = Path(__file__).parent / "sample.k"

    if sample_path.exists():
        result = parser.parse(str(sample_path))

        print(f"\n파싱 결과:")
        print(f"  노드: {len(result.nodes)}개")
        print(f"  파트: {len(result.parts)}개")
        print(f"  엘리먼트: {len(result.elements)}개")
        print(f"  Set: {len(result.sets)}개")
        print(f"  파싱 시간: {result.stats['parse_time_ms']}ms")
        print(f"  백엔드: {result.stats['backend']}")

        print(f"\n노드 목록:")
        for node in result.nodes[:5]:
            print(f"  Node {node.nid}: ({node.x}, {node.y}, {node.z})")

        print(f"\n파트 목록:")
        for part in result.parts:
            print(f"  Part {part.pid}: {part.name} (MID: {part.mid})")

        print(f"\n엘리먼트 목록:")
        for elem in result.elements:
            print(f"  Element {elem.eid}: Part={elem.pid}, Type={elem.element_type}, Nodes={elem.nodes}")

        print(f"\nSet 목록:")
        for s in result.sets:
            if s.set_type == SetType.SEGMENT:
                print(f"  Set {s.sid}: Type={s.set_type.name}, Segments={len(s.segments)}")
            else:
                print(f"  Set {s.sid}: Type={s.set_type.name}, IDs={s.ids}")

        # ID 조회 테스트
        print(f"\nID 조회 테스트:")
        node = result.get_node(1)
        if node:
            print(f"  Node 1: ({node.x}, {node.y}, {node.z})")

        part = result.get_part(1)
        if part:
            print(f"  Part 1: {part.name}")

        set_obj = result.get_set(1)
        if set_obj:
            print(f"  Set 1: Type={set_obj.set_type.name}, Count={set_obj.count}")

        print("\n✓ Python 파서 테스트 통과")
    else:
        print(f"테스트 파일을 찾을 수 없습니다: {sample_path}")


def test_koodynak_compat():
    """KooDynaKeyword 호환성 테스트"""
    print("\n=== KooDynaKeyword 호환성 테스트 ===")

    # 상위 폴더에서 임포트
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    try:
        from KooDynaKeyword import KFileReader, read_kfile

        sample_path = Path(__file__).parent / "sample.k"

        if sample_path.exists():
            reader = read_kfile(str(sample_path))

            print(f"\nKFileReader 결과:")
            print(f"  노드: {reader.node_array().shape}")
            print(f"  파트: {reader.part_array().shape}")
            print(f"  엘리먼트: {reader.element_array().shape}")

            # 기존 API 테스트
            nodes = reader.get_nodes()
            print(f"\nDynaNode 객체:")
            print(f"  NID(0,0): {nodes.NID(0, 0)}")
            print(f"  X(0,0): {nodes.X(0, 0)}")

            parts = reader.get_parts()
            print(f"\nPart 객체:")
            print(f"  NAME(0,0): {parts.NAME(0, 0)}")
            print(f"  PID(0,0): {parts.PID(0, 0)}")

            print("\n✓ KooDynaKeyword 호환성 테스트 통과")
        else:
            print(f"테스트 파일을 찾을 수 없습니다: {sample_path}")

    except ImportError as e:
        print(f"임포트 실패 (C++ 빌드 필요할 수 있음): {e}")


def test_string_parsing():
    """문자열 파싱 테스트"""
    print("\n=== 문자열 파싱 테스트 ===")

    from kfile_parser import KFileParser

    kfile_content = """*KEYWORD
*NODE
       1       0.000000       0.000000       0.000000       0       0
       2       1.000000       0.000000       0.000000       0       0
*PART
Test Part
         1         1       100         0         0         0         0         0
*END
"""

    parser = KFileParser()
    result = parser.parse_string(kfile_content)

    print(f"파싱 결과:")
    print(f"  노드: {len(result.nodes)}개")
    print(f"  파트: {len(result.parts)}개")

    assert len(result.nodes) == 2, f"노드 수가 맞지 않음: {len(result.nodes)}"
    assert len(result.parts) == 1, f"파트 수가 맞지 않음: {len(result.parts)}"

    print("\n✓ 문자열 파싱 테스트 통과")


def test_beam_parsing():
    """ELEMENT_BEAM 파싱 테스트"""
    print("\n=== ELEMENT_BEAM 파싱 테스트 ===")

    from kfile_parser import KFileParser

    kfile_content = """*KEYWORD
*NODE
       1       0.000000       0.000000       0.000000       0       0
       2       1.000000       0.000000       0.000000       0       0
       3       1.000000       1.000000       0.000000       0       0
       4       0.000000       1.000000       0.000000       0       0
*ELEMENT_BEAM
$#   eid     pid      n1      n2      n3
     100       1       1       2       3
     101       1       2       3       4
*END
"""

    parser = KFileParser()
    result = parser.parse_string(kfile_content)

    print(f"파싱된 엘리먼트 수: {len(result.elements)}")
    assert len(result.elements) == 2, f"엘리먼트 수가 맞지 않음: {len(result.elements)}"

    # BEAM 엘리먼트 검증
    beam_elems = [e for e in result.elements if e.element_type == 'beam']
    assert len(beam_elems) == 2, f"BEAM 엘리먼트 수가 맞지 않음: {len(beam_elems)}"

    print(f"  BEAM 엘리먼트:")
    for elem in beam_elems:
        print(f"    EID={elem.eid}, PID={elem.pid}, Nodes={elem.nodes}, Count={elem.node_count}")

    # 첫 번째 BEAM 검증
    assert beam_elems[0].eid == 100, f"EID가 맞지 않음: {beam_elems[0].eid}"
    assert beam_elems[0].pid == 1, f"PID가 맞지 않음: {beam_elems[0].pid}"
    assert beam_elems[0].nodes == [1, 2, 3], f"Nodes가 맞지 않음: {beam_elems[0].nodes}"

    print("\n✓ ELEMENT_BEAM 파싱 테스트 통과")


def test_set_parsing():
    """SET 파싱 테스트"""
    print("\n=== SET 파싱 테스트 ===")

    from kfile_parser import KFileParser
    from kfile_parser.wrapper import SetType

    kfile_content = """*KEYWORD
*SET_NODE_LIST
$#     sid       da1       da2       da3       da4    solver
         1       0.0       0.0       0.0       0.0MECH
$#    nid1      nid2      nid3      nid4      nid5      nid6      nid7      nid8
         1         2         3         4         5         6         7         8
         9        10         0         0         0         0         0         0
*SET_PART_LIST
$#     sid       da1       da2       da3       da4    solver
         2       0.0       0.0       0.0       0.0MECH
$#    pid1      pid2      pid3      pid4      pid5      pid6      pid7      pid8
         1         2         3         0         0         0         0         0
*SET_SEGMENT
$#     sid       da1       da2       da3       da4    solver
         3       0.0       0.0       0.0       0.0MECH
$#      n1        n2        n3        n4
         1         2         3         4
         5         6         7         8
*END
"""

    parser = KFileParser()
    result = parser.parse_string(kfile_content)

    print(f"파싱된 Set 수: {len(result.sets)}")
    assert len(result.sets) == 3, f"Set 수가 맞지 않음: {len(result.sets)} (expected 3)"

    # SET_NODE_LIST 검증
    node_sets = result.get_sets_by_type(SetType.NODE_LIST)
    assert len(node_sets) == 1, f"NODE_LIST 수가 맞지 않음: {len(node_sets)}"
    assert node_sets[0].sid == 1, f"SID가 맞지 않음: {node_sets[0].sid}"
    assert len(node_sets[0].ids) == 10, f"Node ID 수가 맞지 않음: {len(node_sets[0].ids)}"
    print(f"  SET_NODE_LIST: SID={node_sets[0].sid}, IDs={node_sets[0].ids}")

    # SET_PART_LIST 검증
    part_sets = result.get_sets_by_type(SetType.PART_LIST)
    assert len(part_sets) == 1, f"PART_LIST 수가 맞지 않음: {len(part_sets)}"
    assert part_sets[0].sid == 2, f"SID가 맞지 않음: {part_sets[0].sid}"
    assert len(part_sets[0].ids) == 3, f"Part ID 수가 맞지 않음: {len(part_sets[0].ids)}"
    print(f"  SET_PART_LIST: SID={part_sets[0].sid}, IDs={part_sets[0].ids}")

    # SET_SEGMENT 검증
    seg_sets = result.get_sets_by_type(SetType.SEGMENT)
    assert len(seg_sets) == 1, f"SEGMENT 수가 맞지 않음: {len(seg_sets)}"
    assert seg_sets[0].sid == 3, f"SID가 맞지 않음: {seg_sets[0].sid}"
    assert len(seg_sets[0].segments) == 2, f"Segment 수가 맞지 않음: {len(seg_sets[0].segments)}"
    print(f"  SET_SEGMENT: SID={seg_sets[0].sid}, Segments={seg_sets[0].segments}")

    # ID 조회
    set_obj = result.get_set(1)
    assert set_obj is not None, "Set 1을 찾을 수 없음"
    assert set_obj.set_type == SetType.NODE_LIST

    print("\n✓ SET 파싱 테스트 통과")


def test_section_parsing():
    """SECTION 파싱 테스트"""
    print("\n=== SECTION 파싱 테스트 ===")

    from kfile_parser import KFileParser
    from kfile_parser.wrapper import SectionType

    kfile_content = """*KEYWORD
*SECTION_SHELL
$#   secid    elform      shrf       nip     propt   qr/irid     icomp     setyp
         1         2       1.0         2       1.0         0         0         1
$#      t1        t2        t3        t4      nloc     marea      idof    edgset
       1.5       1.5       1.5       1.5       0.0       0.0       0.0       0.0
*SECTION_SOLID
$#   secid    elform       aet
         2         1         0
*SECTION_BEAM
$#   secid    elform      shrf   qr/irid       cst     scoor
         3         1       1.0         0       0.0       0.0
$#     ts1       ts2       tt1       tt2     nsloc     ntloc
       0.5       0.5       0.3       0.3       0.0       0.0
*END
"""

    parser = KFileParser()
    result = parser.parse_string(kfile_content)

    print(f"파싱된 Section 수: {len(result.sections)}")
    assert len(result.sections) == 3, f"Section 수가 맞지 않음: {len(result.sections)} (expected 3)"

    # SECTION_SHELL 검증
    shell_secs = result.get_sections_by_type(SectionType.SHELL)
    assert len(shell_secs) == 1, f"SHELL 섹션 수가 맞지 않음: {len(shell_secs)}"
    assert shell_secs[0].secid == 1, f"SECID가 맞지 않음: {shell_secs[0].secid}"
    assert shell_secs[0].elform == 2, f"ELFORM이 맞지 않음: {shell_secs[0].elform}"
    assert shell_secs[0].nip == 2, f"NIP가 맞지 않음: {shell_secs[0].nip}"
    assert abs(shell_secs[0].thickness[0] - 1.5) < 0.001, f"Thickness가 맞지 않음: {shell_secs[0].thickness[0]}"
    print(f"  SECTION_SHELL: SECID={shell_secs[0].secid}, ELFORM={shell_secs[0].elform}, T1={shell_secs[0].thickness[0]}")

    # SECTION_SOLID 검증
    solid_secs = result.get_sections_by_type(SectionType.SOLID)
    assert len(solid_secs) == 1, f"SOLID 섹션 수가 맞지 않음: {len(solid_secs)}"
    assert solid_secs[0].secid == 2, f"SECID가 맞지 않음: {solid_secs[0].secid}"
    assert solid_secs[0].elform == 1, f"ELFORM이 맞지 않음: {solid_secs[0].elform}"
    assert solid_secs[0].aet == 0, f"AET가 맞지 않음: {solid_secs[0].aet}"
    print(f"  SECTION_SOLID: SECID={solid_secs[0].secid}, ELFORM={solid_secs[0].elform}, AET={solid_secs[0].aet}")

    # SECTION_BEAM 검증
    beam_secs = result.get_sections_by_type(SectionType.BEAM)
    assert len(beam_secs) == 1, f"BEAM 섹션 수가 맞지 않음: {len(beam_secs)}"
    assert beam_secs[0].secid == 3, f"SECID가 맞지 않음: {beam_secs[0].secid}"
    assert beam_secs[0].elform == 1, f"ELFORM이 맞지 않음: {beam_secs[0].elform}"
    assert abs(beam_secs[0].ts[0] - 0.5) < 0.001, f"TS1이 맞지 않음: {beam_secs[0].ts[0]}"
    assert abs(beam_secs[0].tt[0] - 0.3) < 0.001, f"TT1이 맞지 않음: {beam_secs[0].tt[0]}"
    print(f"  SECTION_BEAM: SECID={beam_secs[0].secid}, ELFORM={beam_secs[0].elform}, TS1={beam_secs[0].ts[0]}, TT1={beam_secs[0].tt[0]}")

    # ID 조회 테스트
    sec_obj = result.get_section(1)
    assert sec_obj is not None, "Section 1을 찾을 수 없음"
    assert sec_obj.section_type == SectionType.SHELL
    print(f"  get_section(1) 조회 성공: Type={sec_obj.section_type.name}")

    print("\n✓ SECTION 파싱 테스트 통과")


def test_contact_parsing():
    """CONTACT 파싱 테스트"""
    print("\n=== CONTACT 파싱 테스트 ===")

    from kfile_parser import KFileParser
    from kfile_parser.wrapper import ContactType

    kfile_content = """*KEYWORD
*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE
$#    ssid      msid     sstyp     mstyp    sboxid    mboxid       spr       mpr
         1         2         0         0         0         0         0         0
$#      fs        fd        dc        vc       vdc    penchk        bt        dt
       0.3       0.2       0.0       0.0       0.0         0       0.0     1e+20
$#     sfs       sfm       sst       mst      sfst      sfmt       fsf       vsf
       1.0       1.0       0.0       0.0       1.0       1.0       1.0       1.0
*CONTACT_TIED_NODES_TO_SURFACE
$#    ssid      msid     sstyp     mstyp    sboxid    mboxid       spr       mpr
         3         4         3         0         0         0         0         0
$#      fs        fd        dc        vc       vdc    penchk        bt        dt
       0.0       0.0       0.0       0.0       0.0         0       0.0     1e+20
$#     sfs       sfm       sst       mst      sfst      sfmt       fsf       vsf
       1.0       1.0       0.0       0.0       1.0       1.0       1.0       1.0
*END
"""

    parser = KFileParser()
    result = parser.parse_string(kfile_content)

    print(f"파싱된 Contact 수: {len(result.contacts)}")
    assert len(result.contacts) == 2, f"Contact 수가 맞지 않음: {len(result.contacts)} (expected 2)"

    # AUTOMATIC_SURFACE_TO_SURFACE 검증
    auto_contacts = result.get_contacts_by_type(ContactType.AUTOMATIC_SURFACE_TO_SURFACE)
    assert len(auto_contacts) == 1, f"AUTOMATIC_SURFACE_TO_SURFACE 수가 맞지 않음: {len(auto_contacts)}"
    assert auto_contacts[0].ssid == 1, f"SSID가 맞지 않음: {auto_contacts[0].ssid}"
    assert auto_contacts[0].msid == 2, f"MSID가 맞지 않음: {auto_contacts[0].msid}"
    assert abs(auto_contacts[0].fs - 0.3) < 0.001, f"FS가 맞지 않음: {auto_contacts[0].fs}"
    assert abs(auto_contacts[0].fd - 0.2) < 0.001, f"FD가 맞지 않음: {auto_contacts[0].fd}"
    assert auto_contacts[0].cards_parsed == 3, f"cards_parsed가 맞지 않음: {auto_contacts[0].cards_parsed}"
    print(f"  CONTACT_AUTOMATIC_SURFACE_TO_SURFACE: SSID={auto_contacts[0].ssid}, MSID={auto_contacts[0].msid}, FS={auto_contacts[0].fs}")

    # TIED_NODES_TO_SURFACE 검증
    tied_contacts = result.get_contacts_by_type(ContactType.TIED_NODES_TO_SURFACE)
    assert len(tied_contacts) == 1, f"TIED_NODES_TO_SURFACE 수가 맞지 않음: {len(tied_contacts)}"
    assert tied_contacts[0].ssid == 3, f"SSID가 맞지 않음: {tied_contacts[0].ssid}"
    assert tied_contacts[0].msid == 4, f"MSID가 맞지 않음: {tied_contacts[0].msid}"
    assert tied_contacts[0].sstyp == 3, f"SSTYP가 맞지 않음: {tied_contacts[0].sstyp}"
    print(f"  CONTACT_TIED_NODES_TO_SURFACE: SSID={tied_contacts[0].ssid}, MSID={tied_contacts[0].msid}, SSTYP={tied_contacts[0].sstyp}")

    # ID 조회 테스트
    con_obj = result.get_contact(1)
    assert con_obj is not None, "Contact 1을 찾을 수 없음"
    assert con_obj.contact_type == ContactType.AUTOMATIC_SURFACE_TO_SURFACE
    print(f"  get_contact(1) 조회 성공: Type={con_obj.contact_type.name}")

    print("\n✓ CONTACT 파싱 테스트 통과")


def test_id_title_options():
    """_ID, _TITLE 옵션 파싱 테스트"""
    print("\n=== _ID/_TITLE 옵션 파싱 테스트 ===")

    from kfile_parser import KFileParser
    from kfile_parser.wrapper import ContactType, SectionType, SetType

    # CONTACT_*_TITLE 테스트
    contact_title_content = """*KEYWORD
*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_TITLE
Contact Title Here
$#    ssid      msid     sstyp     mstyp    sboxid    mboxid       spr       mpr
         1         2         0         0         0         0         0         0
$#      fs        fd        dc        vc       vdc    penchk        bt        dt
       0.3       0.2       0.0       0.0       0.0         0       0.0     1e+20
$#     sfs       sfm       sst       mst      sfst      sfmt       fsf       vsf
       1.0       1.0       0.0       0.0       1.0       1.0       1.0       1.0
*END
"""
    parser = KFileParser()
    result = parser.parse_string(contact_title_content)
    assert len(result.contacts) == 1, f"CONTACT_TITLE: 파싱된 개수 {len(result.contacts)}, expected 1"
    assert result.contacts[0].ssid == 1, f"SSID 불일치: {result.contacts[0].ssid}"
    assert abs(result.contacts[0].fs - 0.3) < 0.001, f"FS 불일치: {result.contacts[0].fs}"
    print(f"  CONTACT_*_TITLE: SSID={result.contacts[0].ssid}, FS={result.contacts[0].fs} ✓")

    # CONTACT_*_ID 테스트
    contact_id_content = """*KEYWORD
*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_ID
$#     cid                                                                 title
        99Contact ID Card
$#    ssid      msid     sstyp     mstyp    sboxid    mboxid       spr       mpr
         5         6         0         0         0         0         0         0
$#      fs        fd        dc        vc       vdc    penchk        bt        dt
       0.5       0.4       0.0       0.0       0.0         0       0.0     1e+20
$#     sfs       sfm       sst       mst      sfst      sfmt       fsf       vsf
       1.0       1.0       0.0       0.0       1.0       1.0       1.0       1.0
*END
"""
    result = parser.parse_string(contact_id_content)
    assert len(result.contacts) == 1, f"CONTACT_ID: 파싱된 개수 {len(result.contacts)}, expected 1"
    assert result.contacts[0].ssid == 5, f"SSID 불일치: {result.contacts[0].ssid}"
    assert abs(result.contacts[0].fs - 0.5) < 0.001, f"FS 불일치: {result.contacts[0].fs}"
    print(f"  CONTACT_*_ID: SSID={result.contacts[0].ssid}, FS={result.contacts[0].fs} ✓")

    # SECTION_SHELL_TITLE 테스트
    section_title_content = """*KEYWORD
*SECTION_SHELL_TITLE
Shell Section Title
$#   secid    elform      shrf       nip     propt   qr/irid     icomp     setyp
        10         2       1.0         5       1.0         0         0         1
$#      t1        t2        t3        t4      nloc     marea      idof    edgset
       2.0       2.0       2.0       2.0       0.0       0.0       0.0       0.0
*END
"""
    result = parser.parse_string(section_title_content)
    assert len(result.sections) == 1, f"SECTION_TITLE: 파싱된 개수 {len(result.sections)}, expected 1"
    assert result.sections[0].secid == 10, f"SECID 불일치: {result.sections[0].secid}"
    assert result.sections[0].nip == 5, f"NIP 불일치: {result.sections[0].nip}"
    assert abs(result.sections[0].thickness[0] - 2.0) < 0.001, f"T1 불일치: {result.sections[0].thickness[0]}"
    print(f"  SECTION_SHELL_TITLE: SECID={result.sections[0].secid}, NIP={result.sections[0].nip}, T1={result.sections[0].thickness[0]} ✓")

    # SET_NODE_LIST_TITLE 테스트
    set_title_content = """*KEYWORD
*SET_NODE_LIST_TITLE
Node Set Title Here
$#     sid       da1       da2       da3       da4    solver
        20       0.0       0.0       0.0       0.0MECH
$#    nid1      nid2      nid3      nid4      nid5      nid6      nid7      nid8
         1         2         3         4         0         0         0         0
*END
"""
    result = parser.parse_string(set_title_content)
    assert len(result.sets) == 1, f"SET_TITLE: 파싱된 개수 {len(result.sets)}, expected 1"
    assert result.sets[0].sid == 20, f"SID 불일치: {result.sets[0].sid}"
    assert result.sets[0].count == 4, f"ID 개수 불일치: {result.sets[0].count}, expected 4"
    print(f"  SET_NODE_LIST_TITLE: SID={result.sets[0].sid}, count={result.sets[0].count} ✓")

    # 복합 테스트: _TITLE과 일반 키워드 혼합
    mixed_content = """*KEYWORD
*SECTION_SOLID_TITLE
Solid Section Title
$#   secid    elform       aet
        30         1         0
*SECTION_SOLID
$#   secid    elform       aet
        31         2         1
*END
"""
    result = parser.parse_string(mixed_content)
    assert len(result.sections) == 2, f"Mixed: 파싱된 개수 {len(result.sections)}, expected 2"
    assert result.sections[0].secid == 30, f"첫번째 SECID 불일치: {result.sections[0].secid}"
    assert result.sections[1].secid == 31, f"두번째 SECID 불일치: {result.sections[1].secid}"
    print(f"  Mixed _TITLE + normal: SECID1={result.sections[0].secid}, SECID2={result.sections[1].secid} ✓")

    print("\n✓ _ID/_TITLE 옵션 파싱 테스트 통과")


def test_material_parsing():
    """MATERIAL 파싱 테스트"""
    print("\n=== MATERIAL 파싱 테스트 ===")

    from kfile_parser import KFileParser
    from kfile_parser.wrapper import MaterialType

    kfile_content = """*KEYWORD
*MAT_ELASTIC
$#     mid        ro         e        pr        da        db  not used
         1   7.85e-9     210.0       0.3       0.0       0.0       0.0       0.0
*MAT_PIECEWISE_LINEAR_PLASTICITY
$#     mid        ro         e        pr      sigy      etan      fail      tdel
         2   7.85e-9     210.0       0.3     0.235       0.0      1.05       0.0
$#       c         p      lcss      lcsr        vp
       0.0       0.0         0         0       0.0       0.0       0.0       0.0
*MAT_RIGID
$#     mid        ro         e        pr         n    couple         m     alias
         3   7.85e-9     210.0       0.3       0.0       0.0       0.0       0.0
$#     cmo      con1      con2        a1        a2        a3        v1        v2
       1.0       4.0       7.0       0.0       0.0       0.0       0.0       0.0
$#      v3       lco
       0.0         0
*END
"""

    parser = KFileParser()
    result = parser.parse_string(kfile_content)

    print(f"파싱된 Material 수: {len(result.materials)}")
    assert len(result.materials) == 3, f"Material 수가 맞지 않음: {len(result.materials)} (expected 3)"

    # MAT_ELASTIC 검증
    elastic_mats = result.get_materials_by_type(MaterialType.ELASTIC)
    assert len(elastic_mats) == 1, f"ELASTIC 수가 맞지 않음: {len(elastic_mats)}"
    assert elastic_mats[0].mid == 1, f"MID가 맞지 않음: {elastic_mats[0].mid}"
    assert abs(elastic_mats[0].ro - 7.85e-9) < 1e-15, f"RO가 맞지 않음: {elastic_mats[0].ro}"
    assert abs(elastic_mats[0].e - 210.0) < 0.001, f"E가 맞지 않음: {elastic_mats[0].e}"
    assert abs(elastic_mats[0].pr - 0.3) < 0.001, f"PR가 맞지 않음: {elastic_mats[0].pr}"
    print(f"  MAT_ELASTIC: MID={elastic_mats[0].mid}, RO={elastic_mats[0].ro}, E={elastic_mats[0].e}, PR={elastic_mats[0].pr}")

    # MAT_PIECEWISE_LINEAR_PLASTICITY 검증
    plastic_mats = result.get_materials_by_type(MaterialType.PIECEWISE_LINEAR_PLASTICITY)
    assert len(plastic_mats) == 1, f"PIECEWISE_LINEAR_PLASTICITY 수가 맞지 않음: {len(plastic_mats)}"
    assert plastic_mats[0].mid == 2, f"MID가 맞지 않음: {plastic_mats[0].mid}"
    assert abs(plastic_mats[0].sigy - 0.235) < 0.001, f"SIGY가 맞지 않음: {plastic_mats[0].sigy}"
    assert abs(plastic_mats[0].fail - 1.05) < 0.001, f"FAIL이 맞지 않음: {plastic_mats[0].fail}"
    print(f"  MAT_PIECEWISE_LINEAR_PLASTICITY: MID={plastic_mats[0].mid}, SIGY={plastic_mats[0].sigy}, FAIL={plastic_mats[0].fail}")

    # MAT_RIGID 검증
    rigid_mats = result.get_materials_by_type(MaterialType.RIGID)
    assert len(rigid_mats) == 1, f"RIGID 수가 맞지 않음: {len(rigid_mats)}"
    assert rigid_mats[0].mid == 3, f"MID가 맞지 않음: {rigid_mats[0].mid}"
    assert abs(rigid_mats[0].cmo - 1.0) < 0.001, f"CMO가 맞지 않음: {rigid_mats[0].cmo}"
    assert abs(rigid_mats[0].con1 - 4.0) < 0.001, f"CON1이 맞지 않음: {rigid_mats[0].con1}"
    assert abs(rigid_mats[0].con2 - 7.0) < 0.001, f"CON2가 맞지 않음: {rigid_mats[0].con2}"
    print(f"  MAT_RIGID: MID={rigid_mats[0].mid}, CMO={rigid_mats[0].cmo}, CON1={rigid_mats[0].con1}, CON2={rigid_mats[0].con2}")

    # ID 조회 테스트
    mat_obj = result.get_material(1)
    assert mat_obj is not None, "Material 1을 찾을 수 없음"
    assert mat_obj.material_type == MaterialType.ELASTIC
    print(f"  get_material(1) 조회 성공: Type={mat_obj.material_type.name}")

    # Raw card data 검증
    assert len(elastic_mats[0].cards) >= 1, "Card data가 없음"
    assert abs(elastic_mats[0].get_card_value(0, 0) - 1.0) < 0.001, "Card value 불일치"
    print(f"  Raw card data: {elastic_mats[0].cards}")

    print("\n✓ MATERIAL 파싱 테스트 통과")


def test_material_title_parsing():
    """MATERIAL _TITLE 옵션 파싱 테스트"""
    print("\n=== MATERIAL _TITLE 파싱 테스트 ===")

    from kfile_parser import KFileParser
    from kfile_parser.wrapper import MaterialType

    kfile_content = """*KEYWORD
*MAT_ELASTIC_TITLE
Steel Material
$#     mid        ro         e        pr        da        db  not used
        10  7.85e-09     200.0       0.3       0.0       0.0       0.0       0.0
*MAT_ORTHOTROPIC_ELASTIC_TITLE
CFRP Composite
$#     mid        ro        ea        eb        ec      prba      prca      prcb
        20  1.58e-09    130000     9000.0     9000.0      0.02      0.02      0.30
$#     gab       gbc       gca      aopt         g      sigf
      5200      3000      5200         0       0.0       0.0       0.0       0.0
*END
"""

    parser = KFileParser()
    result = parser.parse_string(kfile_content)

    print(f"파싱된 Material 수: {len(result.materials)}")
    assert len(result.materials) == 2, f"Material 수가 맞지 않음: {len(result.materials)} (expected 2)"

    # MAT_ELASTIC_TITLE 검증
    elastic_mats = result.get_materials_by_type(MaterialType.ELASTIC)
    assert len(elastic_mats) == 1, f"ELASTIC 수가 맞지 않음"
    assert elastic_mats[0].mid == 10, f"MID가 맞지 않음: {elastic_mats[0].mid}"
    assert abs(elastic_mats[0].e - 200.0) < 0.001, f"E가 맞지 않음: {elastic_mats[0].e}"
    print(f"  MAT_ELASTIC_TITLE: MID={elastic_mats[0].mid}, E={elastic_mats[0].e}")

    # MAT_ORTHOTROPIC_ELASTIC_TITLE 검증
    ortho_mats = result.get_materials_by_type(MaterialType.ORTHOTROPIC_ELASTIC)
    assert len(ortho_mats) == 1, f"ORTHOTROPIC_ELASTIC 수가 맞지 않음"
    assert ortho_mats[0].mid == 20, f"MID가 맞지 않음: {ortho_mats[0].mid}"
    assert abs(ortho_mats[0].e - 130000.0) < 1.0, f"E(EA)가 맞지 않음: {ortho_mats[0].e}"
    assert abs(ortho_mats[0].gab - 5200.0) < 1.0, f"GAB가 맞지 않음: {ortho_mats[0].gab}"
    print(f"  MAT_ORTHOTROPIC_ELASTIC_TITLE: MID={ortho_mats[0].mid}, EA={ortho_mats[0].e}, GAB={ortho_mats[0].gab}")

    print("\n✓ MATERIAL _TITLE 파싱 테스트 통과")


def test_composite_material_parsing():
    """복합재 MATERIAL 파싱 테스트"""
    print("\n=== 복합재 MATERIAL 파싱 테스트 ===")

    from kfile_parser import KFileParser
    from kfile_parser.wrapper import MaterialType

    kfile_content = """*KEYWORD
*MAT_054
$#     mid        ro        ea        eb        ec      prba      tau1    gamma1
       100  1.58e-09    130000     9000.0       0.0      0.02       0.0       0.0
$#     gab       gbc       gca     kfail      aopt     maxp
      5200      3000      5200       0.0         0       0.0       0.0       0.0
$#      xc        xt        yc        yt        sc      crit      beta
       1.5       1.9       0.2      0.05      0.07       0.0       0.0       0.0
$#    tfail      alph      soft      fbrt     ycfac    dfailm    dfails    dfailt
       0.0       0.0       1.0       0.5       1.8       0.0       0.0       0.0
$#    efs      pvrt      puck      sofs
       0.0       0.0         0       0.0       0.0       0.0       0.0       0.0
$#  softg     lcxc     lcxt     lcyc     lcyt     lcsc      dt
       0.0         0         0         0         0         0       0.0       0.0
*END
"""

    parser = KFileParser()
    result = parser.parse_string(kfile_content)

    print(f"파싱된 Material 수: {len(result.materials)}")
    assert len(result.materials) == 1, f"Material 수가 맞지 않음: {len(result.materials)} (expected 1)"

    # MAT_054 검증
    comp_mats = result.get_materials_by_type(MaterialType.COMPOSITE_DAMAGE)
    assert len(comp_mats) == 1, f"COMPOSITE_DAMAGE 수가 맞지 않음: {len(comp_mats)}"
    mat = comp_mats[0]

    assert mat.mid == 100, f"MID가 맞지 않음: {mat.mid}"
    assert abs(mat.ro - 1.58e-9) < 1e-15, f"RO가 맞지 않음: {mat.ro}"
    assert abs(mat.e - 130000.0) < 1.0, f"EA가 맞지 않음: {mat.e}"
    assert abs(mat.eb - 9000.0) < 1.0, f"EB가 맞지 않음: {mat.eb}"
    assert abs(mat.gab - 5200.0) < 1.0, f"GAB가 맞지 않음: {mat.gab}"
    print(f"  MAT_054: MID={mat.mid}, EA={mat.e}, EB={mat.eb}, GAB={mat.gab}")

    # Strength values (Card 3)
    assert abs(mat.xc - 1.5) < 0.001, f"XC가 맞지 않음: {mat.xc}"
    assert abs(mat.xt - 1.9) < 0.001, f"XT가 맞지 않음: {mat.xt}"
    assert abs(mat.yc - 0.2) < 0.001, f"YC가 맞지 않음: {mat.yc}"
    assert abs(mat.yt - 0.05) < 0.001, f"YT가 맞지 않음: {mat.yt}"
    assert abs(mat.sc - 0.07) < 0.001, f"SC가 맞지 않음: {mat.sc}"
    print(f"  Strength: XC={mat.xc}, XT={mat.xt}, YC={mat.yc}, YT={mat.yt}, SC={mat.sc}")

    # Raw card count
    assert len(mat.cards) == 6, f"Card 수가 맞지 않음: {len(mat.cards)} (expected 6)"
    print(f"  Total cards parsed: {len(mat.cards)}")

    print("\n✓ 복합재 MATERIAL 파싱 테스트 통과")


def test_include_parsing():
    """INCLUDE 파싱 테스트"""
    print("\n=== INCLUDE 파싱 테스트 ===")

    from kfile_parser import KFileParser

    kfile_content = """*KEYWORD
*INCLUDE
/path/to/material.k
*INCLUDE
/path/to/nodes.k
*END
"""

    parser = KFileParser()
    result = parser.parse_string(kfile_content)

    print(f"파싱된 Include 수: {len(result.includes)}")
    assert len(result.includes) == 2, f"Include 수가 맞지 않음: {len(result.includes)} (expected 2)"

    assert result.includes[0].filepath == "/path/to/material.k", f"filepath 불일치: {result.includes[0].filepath}"
    assert result.includes[1].filepath == "/path/to/nodes.k", f"filepath 불일치: {result.includes[1].filepath}"
    print(f"  Include 1: {result.includes[0].filepath}")
    print(f"  Include 2: {result.includes[1].filepath}")

    print("\n✓ INCLUDE 파싱 테스트 통과")


def test_curve_parsing():
    """DEFINE_CURVE 파싱 테스트"""
    print("\n=== DEFINE_CURVE 파싱 테스트 ===")

    from kfile_parser import KFileParser

    kfile_content = """*KEYWORD
*DEFINE_CURVE
$#    lcid      sidr       sfa       sfo      offa      offo    dattyp
         1         0       1.0       1.0       0.0       0.0         0
$#                a1                  o1
                 0.0                 0.0
                 1.0               100.0
                 2.0               200.0
*DEFINE_CURVE_TITLE
Load Curve
$#    lcid      sidr       sfa       sfo      offa      offo    dattyp
         2         0       1.0       2.0       0.0       0.0         0
$#                a1                  o1
                 0.0                 0.0
                 1.0                50.0
*END
"""

    parser = KFileParser()
    result = parser.parse_string(kfile_content)

    print(f"파싱된 Curve 수: {len(result.curves)}")
    assert len(result.curves) == 2, f"Curve 수가 맞지 않음: {len(result.curves)} (expected 2)"

    # 첫 번째 curve 검증
    curve1 = result.curves[0]
    assert curve1.lcid == 1, f"LCID가 맞지 않음: {curve1.lcid}"
    assert len(curve1.points) == 3, f"Point 수가 맞지 않음: {len(curve1.points)} (expected 3)"
    print(f"  Curve 1: LCID={curve1.lcid}, Points={len(curve1.points)}")

    # 두 번째 curve 검증 (_TITLE)
    curve2 = result.curves[1]
    assert curve2.lcid == 2, f"LCID가 맞지 않음: {curve2.lcid}"
    assert abs(curve2.sfo - 2.0) < 0.001, f"SFO가 맞지 않음: {curve2.sfo}"
    assert len(curve2.points) == 2, f"Point 수가 맞지 않음: {len(curve2.points)} (expected 2)"
    print(f"  Curve 2: LCID={curve2.lcid}, SFO={curve2.sfo}, Points={len(curve2.points)}")

    print("\n✓ DEFINE_CURVE 파싱 테스트 통과")


def test_boundary_spc_parsing():
    """BOUNDARY_SPC 파싱 테스트"""
    print("\n=== BOUNDARY_SPC 파싱 테스트 ===")

    from kfile_parser import KFileParser

    kfile_content = """*KEYWORD
*BOUNDARY_SPC_SET
$#    nsid       cid      dofx      dofy      dofz     dofrx     dofry     dofrz
         1         0         1         1         1         0         0         0
         2         0         1         1         0         0         0         0
*BOUNDARY_SPC_NODE
$#     nid       dof       vad
       100         1         0
       101         2         0
*END
"""

    parser = KFileParser()
    result = parser.parse_string(kfile_content)

    print(f"파싱된 BoundarySPC 수: {len(result.boundary_spcs)}")
    assert len(result.boundary_spcs) == 4, f"BoundarySPC 수가 맞지 않음: {len(result.boundary_spcs)} (expected 4)"

    # SET 형식 검증
    spc0 = result.boundary_spcs[0]
    assert spc0.nid == 1, f"NID가 맞지 않음: {spc0.nid}"
    assert spc0.dofx == 1, f"DOFX가 맞지 않음: {spc0.dofx}"
    assert spc0.dofy == 1, f"DOFY가 맞지 않음: {spc0.dofy}"
    assert spc0.dofz == 1, f"DOFZ가 맞지 않음: {spc0.dofz}"
    print(f"  SPC_SET 1: NID={spc0.nid}, DOFs=[{spc0.dofx},{spc0.dofy},{spc0.dofz}]")

    # NODE 형식 검증
    spc2 = result.boundary_spcs[2]
    assert spc2.nid == 100, f"NID가 맞지 않음: {spc2.nid}"
    assert spc2.dof == 1, f"DOF가 맞지 않음: {spc2.dof}"
    print(f"  SPC_NODE: NID={spc2.nid}, DOF={spc2.dof}")

    print("\n✓ BOUNDARY_SPC 파싱 테스트 통과")


def test_boundary_motion_parsing():
    """BOUNDARY_PRESCRIBED_MOTION 파싱 테스트"""
    print("\n=== BOUNDARY_PRESCRIBED_MOTION 파싱 테스트 ===")

    from kfile_parser import KFileParser

    kfile_content = """*KEYWORD
*BOUNDARY_PRESCRIBED_MOTION_NODE
$#     nid       dof       vad      lcid        sf       vid     death     birth
         1         3         2         1       1.0         0       0.0       0.0
         2         2         2         2       2.0         0       0.0       0.0
*END
"""

    parser = KFileParser()
    result = parser.parse_string(kfile_content)

    print(f"파싱된 BoundaryMotion 수: {len(result.boundary_motions)}")
    assert len(result.boundary_motions) == 2, f"BoundaryMotion 수가 맞지 않음: {len(result.boundary_motions)} (expected 2)"

    motion1 = result.boundary_motions[0]
    assert motion1.nid == 1, f"NID가 맞지 않음: {motion1.nid}"
    assert motion1.dof == 3, f"DOF가 맞지 않음: {motion1.dof}"
    assert motion1.vad == 2, f"VAD가 맞지 않음: {motion1.vad}"
    assert motion1.lcid == 1, f"LCID가 맞지 않음: {motion1.lcid}"
    assert abs(motion1.sf - 1.0) < 0.001, f"SF가 맞지 않음: {motion1.sf}"
    print(f"  Motion 1: NID={motion1.nid}, DOF={motion1.dof}, VAD={motion1.vad}, LCID={motion1.lcid}")

    print("\n✓ BOUNDARY_PRESCRIBED_MOTION 파싱 테스트 통과")


def test_load_parsing():
    """LOAD 파싱 테스트"""
    print("\n=== LOAD 파싱 테스트 ===")

    from kfile_parser import KFileParser

    kfile_content = """*KEYWORD
*LOAD_NODE_POINT
$#     nid       dof      lcid        sf       cid        m1        m2        m3
         1         3         1       1.0         0         0         0         0
*LOAD_SEGMENT
$#    lcid        sf        at        n1        n2        n3        n4
         1       1.0       0.0         1         2         3         4
         2       2.0       0.0         5         6         7         8
*LOAD_BODY_Z
$#    lcid        sf    lciddr        xc        yc        zc       cid
         1       9.8         0       0.0       0.0       0.0         0
*END
"""

    parser = KFileParser()
    result = parser.parse_string(kfile_content)

    # LOAD_NODE 검증
    print(f"파싱된 LoadNode 수: {len(result.load_nodes)}")
    assert len(result.load_nodes) == 1, f"LoadNode 수가 맞지 않음: {len(result.load_nodes)} (expected 1)"

    load_node = result.load_nodes[0]
    assert load_node.nid == 1, f"NID가 맞지 않음: {load_node.nid}"
    assert load_node.dof == 3, f"DOF가 맞지 않음: {load_node.dof}"
    assert load_node.lcid == 1, f"LCID가 맞지 않음: {load_node.lcid}"
    print(f"  LoadNode: NID={load_node.nid}, DOF={load_node.dof}, LCID={load_node.lcid}")

    # LOAD_SEGMENT 검증
    print(f"파싱된 LoadSegment 수: {len(result.load_segments)}")
    assert len(result.load_segments) == 2, f"LoadSegment 수가 맞지 않음: {len(result.load_segments)} (expected 2)"

    seg1 = result.load_segments[0]
    assert seg1.lcid == 1, f"LCID가 맞지 않음: {seg1.lcid}"
    assert seg1.n1 == 1, f"N1이 맞지 않음: {seg1.n1}"
    assert seg1.n4 == 4, f"N4가 맞지 않음: {seg1.n4}"
    print(f"  LoadSegment 1: LCID={seg1.lcid}, Nodes=[{seg1.n1},{seg1.n2},{seg1.n3},{seg1.n4}]")

    # LOAD_BODY 검증
    print(f"파싱된 LoadBody 수: {len(result.load_bodies)}")
    assert len(result.load_bodies) == 1, f"LoadBody 수가 맞지 않음: {len(result.load_bodies)} (expected 1)"

    body = result.load_bodies[0]
    assert body.direction == 3, f"Direction이 맞지 않음: {body.direction} (expected 3 for Z)"
    assert body.lcid == 1, f"LCID가 맞지 않음: {body.lcid}"
    assert abs(body.sf - 9.8) < 0.001, f"SF가 맞지 않음: {body.sf}"
    print(f"  LoadBody: Direction={body.direction}(Z), LCID={body.lcid}, SF={body.sf}")

    print("\n✓ LOAD 파싱 테스트 통과")


if __name__ == "__main__":
    test_python_fallback()
    test_string_parsing()
    test_beam_parsing()
    test_set_parsing()
    test_section_parsing()
    test_contact_parsing()
    test_id_title_options()
    test_material_parsing()
    test_material_title_parsing()
    test_composite_material_parsing()
    test_include_parsing()
    test_curve_parsing()
    test_boundary_spc_parsing()
    test_boundary_motion_parsing()
    test_load_parsing()
    test_koodynak_compat()
    print("\n=== 모든 테스트 완료 ===")
