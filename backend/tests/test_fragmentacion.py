from app.procesamiento.fragmentacion import dividir_en_fragmentos

ORACIONES = "".join(f"Esta es la oración número {i} del documento de prueba. " for i in range(100))


def test_texto_corto_genera_un_solo_fragmento():
    fragmentos = dividir_en_fragmentos(["Un texto corto."], tamano=1000, solapamiento=200)

    assert len(fragmentos) == 1
    assert fragmentos[0].pagina == 1
    assert fragmentos[0].contenido == "Un texto corto."


def test_ningun_fragmento_supera_el_tamano():
    fragmentos = dividir_en_fragmentos([ORACIONES], tamano=300, solapamiento=80)

    assert len(fragmentos) > 1
    assert all(len(f.contenido) <= 300 for f in fragmentos)


def test_fragmentos_consecutivos_se_solapan():
    fragmentos = dividir_en_fragmentos([ORACIONES], tamano=300, solapamiento=80)

    # El inicio de cada fragmento aparece al final del anterior
    for anterior, siguiente in zip(fragmentos, fragmentos[1:]):
        assert siguiente.contenido[:30] in anterior.contenido


def test_cada_fragmento_pertenece_a_una_sola_pagina():
    fragmentos = dividir_en_fragmentos(["Página uno.", "", "Página tres."], tamano=1000, solapamiento=200)

    assert [(f.pagina, f.contenido) for f in fragmentos] == [(1, "Página uno."), (3, "Página tres.")]
    assert [f.orden for f in fragmentos] == [0, 1]


def test_palabra_mas_larga_que_el_tamano_se_corta():
    fragmentos = dividir_en_fragmentos(["x" * 250], tamano=100, solapamiento=0)

    assert all(len(f.contenido) <= 100 for f in fragmentos)
    assert "".join(f.contenido for f in fragmentos) == "x" * 250