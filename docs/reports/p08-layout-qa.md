# QA do plano - STUDY (R14 pré-modelo)

Veredito: **PASS** (25 verificações; 0 falhas; 5 aguardando o modelo)

Hash do layout: 9410f296b0d3a258a51971a6e2a35cd404f8018ca28ba5d6f36003516808539d

Esta passagem julga o plano e o programa. Ela **não** julga o modelo
Revit, que ainda não existe: as verificações de modelo aparecem como
MODEL_PENDING e não como aprovadas.

| verificação | escopo | situação | detalhe |
| --- | --- | --- | --- |
| program.every_room_placed | PROGRAM | PASS | todos os 52 ambientes do programa foram colocados |
| program.areas_are_exact | PROGRAM | PASS | cada área líquida é exatamente a do programa |
| program.reconciliation | PROGRAM | PASS | reconciliação do programa: PASS |
| program.enclosed_estimate | PROGRAM | PASS | área fechada 784.88 m2 dentro de 783-814 m2 |
| program.covered_estimate | PROGRAM | PASS | área coberta 918.56 m2 dentro de 850-950 m2 |
| program.capacity_is_20 | PROGRAM | PASS | capacidade fixada em 20 pessoas |
| program.external_total_is_260 | PROGRAM | PASS | programa externo de 260 m2 preservado |
| plan.no_room_overlap | PLAN | PASS | nenhuma sobreposição entre ambientes |
| plan.gallery_is_clear | PLAN | PASS | a galeria não invade nenhum ambiente |
| plan.every_room_on_the_gallery | PLAN | PASS | todos os 52 ambientes abrem para a galeria |
| plan.gallery_width | PLAN | PASS | galeria com 1.50 m, acima do mínimo acessível de 1,50 m |
| plan.room_minimum_dimension | PLAN | PASS | nenhum ambiente abaixo de 1,00 m no menor lado |
| plan.patio_is_open_ground | PLAN | PASS | pátio protegido de 712.97 m2, sem sobreposição com a construção |
| plan.rooms_inside_the_plate | PLAN | PASS | todos os ambientes estão dentro da projeção construída |
| plan.privacy_gradient_recorded | PLAN | PASS | o gradiente de privacidade está registrado em todos os ambientes |
| plan.residential_faces_the_patio | PLAN | PASS | os 18 ambientes residenciais voltam-se ao pátio |
| plan.services_on_the_street_face | PLAN | PASS | os 15 ambientes de serviço ficam na face da rua |
| plan.deterministic_hash | PLAN | PASS | o plano carrega hash de conteúdo 9410f296b0d3a258 |
| site.building_inside_the_study_boundary | PLAN | PASS | a construção está dentro do quadrado de estudo de 24.135 m2 |
| site.setback_from_the_boundary | PLAN | PASS | recuos de 5.00 m e 5.00 m a partir das divisas oeste e sul |
| model.elements_exist_in_revit | MODEL_PENDING | FAIL | requer o modelo Revit; não avaliado nesta passagem |
| model.rooms_bounded_and_placed | MODEL_PENDING | FAIL | requer o modelo Revit; não avaliado nesta passagem |
| model.sheet_set_published | MODEL_PENDING | FAIL | requer o modelo Revit; não avaliado nesta passagem |
| model.exports_ifc_pdf_dwg | MODEL_PENDING | FAIL | requer o modelo Revit; não avaliado nesta passagem |
| model.cold_reopen_verified | MODEL_PENDING | FAIL | requer o modelo Revit; não avaliado nesta passagem |
