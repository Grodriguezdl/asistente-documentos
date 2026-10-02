from fastapi.testclient import TestClient

from app.main import app

cliente = TestClient(app)


def test_rechaza_archivos_que_no_son_pdf():
    respuesta = cliente.post(
        "/api/documentos",
        files={"archivo": ("notas.txt", b"hola", "text/plain")},
    )

    assert respuesta.status_code == 400
    assert "PDF" in respuesta.json()["detail"]


def test_rechaza_archivos_renombrados_como_pdf():
    respuesta = cliente.post(
        "/api/documentos",
        files={"archivo": ("falso.pdf", b"esto no es un pdf", "application/pdf")},
    )

    assert respuesta.status_code == 400
    assert respuesta.json()["detail"] == "El archivo no es un PDF válido."