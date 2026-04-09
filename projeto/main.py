from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from database import create_db_and_tables, get_session
from models import Autor, Livro

app = FastAPI()
templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


def normalizar(texto: str) -> str:
    return " ".join(texto.split()).casefold()


def listar_autores(db: Session):
    stmt = select(Autor).order_by(Autor.nome)
    return db.exec(stmt).all()


def listar_livros(db: Session, busca: str = "", autor_id_filtro: int | None = None):
    stmt = select(Livro).join(Autor)

    if busca:
        termo = normalizar(busca)
        stmt = stmt.where(Livro.titulo.ilike(f"%{termo}%"))

    if autor_id_filtro is not None:
        stmt = stmt.where(Livro.autor_id == autor_id_filtro)

    stmt = stmt.order_by(Livro.titulo)
    return db.exec(stmt).all()


def render_autores(request: Request, db: Session, erro: str = ""):
    autores = listar_autores(db)
    return templates.TemplateResponse(
        request=request,
        name="partials/autores.html",
        context={
            "autores": autores,
            "erro": erro,
        },
    )

def render_livros(
    request: Request,
    db: Session,
    busca: str = "",
    autor_id_filtro: int | None = None,
    erro: str = "",
):
    autores = listar_autores(db)
    livros = listar_livros(db, busca=busca, autor_id_filtro=autor_id_filtro)
    return templates.TemplateResponse(
        request=request,
        name="partials/livros.html",
        context={
            "autores": autores,
            "livros": livros,
            "busca": busca,
            "busca_url": busca,
            "autor_id_filtro": autor_id_filtro,
            "erro": erro,
        },
    )


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={},
    )


@app.get("/autores", response_class=HTMLResponse)
def pagina_autores(request: Request, db: Session = Depends(get_session)):
    return render_autores(request, db)


@app.post("/autores", response_class=HTMLResponse)
def criar_autor(
    request: Request,
    nome: str = Form(...),
    db: Session = Depends(get_session),
):
    nome_limpo = " ".join(nome.split())
    erro = ""

    if not nome_limpo:
        erro = "Informe um nome."
    else:
        existe = db.exec(
            select(Autor).where(Autor.nome.ilike(nome_limpo))
        ).first()

        if existe:
            erro = "Autor já cadastrado."
        else:
            db.add(Autor(nome=nome_limpo))
            db.commit()

    response = render_autores(request, db, erro=erro)
    
    if not erro:
        response.headers["HX-Trigger"] = "autorAdicionado"
        
    return response


@app.get("/livros", response_class=HTMLResponse)
def pagina_livros(
    request: Request,
    busca: str = "",
    autor_id: str | None = None,
    db: Session = Depends(get_session),
):
    id_filtro = int(autor_id) if autor_id and autor_id.isdigit() else None
    return render_livros(request, db, busca=busca, autor_id_filtro=id_filtro)


@app.post("/livros", response_class=HTMLResponse)
def criar_livro(
    request: Request,
    titulo: str = Form(...),
    avaliacao: int = Form(...),
    autor_id: int = Form(...),
    busca: str = Form(""),
    autor_id_filtro: str = Form(""), 
    db: Session = Depends(get_session),
):
    titulo_limpo = " ".join(titulo.split())
    erro = ""

    if not titulo_limpo:
        erro = "Informe um título."
    elif avaliacao < 0 or avaliacao > 5:
        erro = "A avaliação deve estar entre 0 e 5."
    else:
        existe = db.exec(
            select(Livro).where(
                Livro.titulo.ilike(titulo_limpo),
                Livro.autor_id == autor_id, 
            )
        ).first()

        if existe:
            erro = "Esse livro já foi adicionado."
        else:
            livro = Livro(titulo=titulo_limpo, avaliacao=avaliacao, autor_id=autor_id)
            db.add(livro)
            db.commit()

    id_filtro = int(autor_id_filtro) if autor_id_filtro.isdigit() else None

    response = render_livros(
        request,
        db,
        busca=busca,
        autor_id_filtro=id_filtro,
        erro=erro,
    )

    if not erro:
        response.headers["HX-Trigger"] = "autorAdicionado"
    
    return response

@app.get("/livros/{livro_id}/editar-nota", response_class=HTMLResponse)
def modo_edicao_nota(livro_id: int, db: Session = Depends(get_session)):
    livro = db.get(Livro, livro_id)
    if not livro: return ""
    
    return f"""
    <tr id="livro-{livro.id}" class="table-warning">
        <td class="fw-bold">{livro.titulo}</td>
        <td>{livro.autor.nome}</td>
        <td>
            <form hx-put="/livros/{livro.id}/reavaliar" 
                  hx-target="#livro-{livro.id}" 
                  hx-swap="outerHTML" 
                  class="d-flex gap-2">
                <input type="number" name="nova_avaliacao" value="{livro.avaliacao}" 
                       min="0" max="5" class="form-control form-control-sm" 
                       style="width: 70px;" autofocus>
                <button type="submit" class="btn btn-sm btn-success">Confirmar</button>
            </form>
        </td>
        <td class="text-end">
            <button class="btn btn-sm btn-link text-secondary" 
                    hx-get="/livros" hx-target="#livros-area">Cancelar</button>
        </td>
    </tr>
    """

@app.put("/livros/{livro_id}/reavaliar", response_class=HTMLResponse)
def atualizar_avaliacao(livro_id: int, nova_avaliacao: int = Form(...), db: Session = Depends(get_session)):
    livro = db.get(Livro, livro_id)
    if livro:
        livro.avaliacao = nova_avaliacao
        db.add(livro)
        db.commit()
        db.refresh(livro)

    return f"""
    <tr id="livro-{livro.id}">
        <td class="fw-bold">{livro.titulo}</td>
        <td>{livro.autor.nome}</td>
        <td>{livro.avaliacao} / 5</td>
        <td class="text-end">
            <div class="btn-group">
                <button class="btn btn-sm btn-outline-primary" 
                        hx-get="/livros/{livro.id}/editar-nota" 
                        hx-target="#livro-{livro.id}" hx-swap="outerHTML">
                    Reavaliar
                </button>
                <button class="btn btn-sm btn-outline-danger" 
                        hx-delete="/livros/{livro.id}" hx-target="#livros-area">
                    Excluir
                </button>
            </div>
        </td>
    </tr>
    """


@app.delete("/livros/{livro_id}", response_class=HTMLResponse)
def deletar_livro(
    request: Request,
    livro_id: int,
    busca: str = "",
    autor_id_filtro: str = "",
    db: Session = Depends(get_session),
):
    id_filtro = int(autor_id_filtro) if autor_id_filtro.isdigit() else None
    
    livro = db.get(Livro, livro_id)
    if livro is not None:
        db.delete(livro)
        db.commit()

    response = render_livros(
        request,
        db,
        busca=busca,
        autor_id_filtro=id_filtro,
    )

    response.headers["HX-Trigger"] = "autorAdicionado" #atualiza número de livros cadastrados
    
    return response

@app.delete("/autores/{autor_id}", response_class=HTMLResponse)
def deletar_autor(
    request: Request,
    autor_id: int, 
    db: Session = Depends(get_session)
):
    autor = db.get(Autor, autor_id)
    if not autor:
        return render_autores(request, db)

    db.delete(autor)
    db.commit()

    response = render_autores(request, db)
    response.headers["HX-Trigger"] = "autorAdicionado"
    return response