*KEYWORD
*TITLE
Sample K-file for testing
$
*NODE
$#   nid               x               y               z      tc      rc
       1       0.000000       0.000000       0.000000       0       0
       2       1.000000       0.000000       0.000000       0       0
       3       1.000000       1.000000       0.000000       0       0
       4       0.000000       1.000000       0.000000       0       0
       5       0.000000       0.000000       1.000000       0       0
       6       1.000000       0.000000       1.000000       0       0
       7       1.000000       1.000000       1.000000       0       0
       8       0.000000       1.000000       1.000000       0       0
$
*PART
Test Part 1
         1         1       100         0         0         0         0         0
*PART
Test Part 2
         2         2       200         0         0         0         0         0
$
*ELEMENT_SHELL
$#   eid     pid      n1      n2      n3      n4      n5      n6      n7      n8
       1       1       1       2       3       4       0       0       0       0
       2       1       5       6       7       8       0       0       0       0
$
*ELEMENT_SOLID
$#   eid     pid      n1      n2      n3      n4      n5      n6      n7      n8
      10       2       1       2       3       4       5       6       7       8
$
*ELEMENT_BEAM
$#   eid     pid      n1      n2      n3
     100       1       1       2       3
     101       1       2       3       4
$
*SET_NODE_LIST
$#     sid       da1       da2       da3       da4    solver
         1       0.0       0.0       0.0       0.0MECH
$#    nid1      nid2      nid3      nid4      nid5      nid6      nid7      nid8
         1         2         3         4         5         6         7         8
$
*SET_PART_LIST
$#     sid       da1       da2       da3       da4    solver
         2       0.0       0.0       0.0       0.0MECH
$#    pid1      pid2      pid3      pid4      pid5      pid6      pid7      pid8
         1         2         0         0         0         0         0         0
$
*SET_SEGMENT
$#     sid       da1       da2       da3       da4    solver
         3       0.0       0.0       0.0       0.0MECH
$#      n1        n2        n3        n4
         1         2         3         4
         5         6         7         8
$
*SET_SHELL
$#     sid       da1       da2       da3       da4    solver
         4       0.0       0.0       0.0       0.0MECH
$#    eid1      eid2      eid3      eid4      eid5      eid6      eid7      eid8
         1         2         0         0         0         0         0         0
$
*SET_SOLID
$#     sid       da1       da2       da3       da4    solver
         5       0.0       0.0       0.0       0.0MECH
$#    eid1      eid2      eid3      eid4      eid5      eid6      eid7      eid8
        10         0         0         0         0         0         0         0
$
*SECTION_SHELL
$#   secid    elform      shrf       nip     propt   qr/irid     icomp     setyp
         1         2       1.0         2       1.0         0         0         1
$#      t1        t2        t3        t4      nloc     marea      idof    edgset
       1.5       1.5       1.5       1.5       0.0       0.0       0.0       0.0
$
*SECTION_SOLID
$#   secid    elform       aet
         2         1         0
$
*SECTION_BEAM
$#   secid    elform      shrf   qr/irid       cst     scoor
         3         1       1.0         0       0.0       0.0
$#     ts1       ts2       tt1       tt2     nsloc     ntloc
       0.5       0.5       0.3       0.3       0.0       0.0
$
*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE
$#    ssid      msid     sstyp     mstyp    sboxid    mboxid       spr       mpr
         1         2         0         0         0         0         0         0
$#      fs        fd        dc        vc       vdc    penchk        bt        dt
       0.3       0.2       0.0       0.0       0.0         0       0.0     1e+20
$#     sfs       sfm       sst       mst      sfst      sfmt       fsf       vsf
       1.0       1.0       0.0       0.0       1.0       1.0       1.0       1.0
$
*CONTACT_TIED_NODES_TO_SURFACE
$#    ssid      msid     sstyp     mstyp    sboxid    mboxid       spr       mpr
         3         4         3         0         0         0         0         0
$#      fs        fd        dc        vc       vdc    penchk        bt        dt
       0.0       0.0       0.0       0.0       0.0         0       0.0     1e+20
$#     sfs       sfm       sst       mst      sfst      sfmt       fsf       vsf
       1.0       1.0       0.0       0.0       1.0       1.0       1.0       1.0
$
*END
