from fastapi import FastAPI, Form, Cookie, Response, Depends, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI()

usuarios = {}

class Usuario(BaseModel):
    nome: str
    senha: str
    bio: str

def obter_usuario_logado(session_id: str = Cookie(None)):
    return usuarios[session_id]

@app.get("/", response_class=HTMLResponse)
def pagina_registro():
    return """
    <html>
        <body>
            <h1>Criar Novo Usuário</h1>
            <input id="nome" placeholder="Nome">
            <input id="senha" type="password" placeholder="Senha">
            <input id="bio" placeholder="Bio">
            <button onclick="criarUsuario()">Cadastrar</button>

            <script>
                async function criarUsuario() {
                    const dados = {
                        nome: document.getElementById('nome').value,
                        senha: document.getElementById('senha').value,
                        bio: document.getElementById('bio').value
                    };
                    
                    const res = await fetch('/users', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(dados)
                    });

                    alert('Usuário criado');
                }
            </script>
            <br><a href="/login">Ir para Login</a>
        </body>
    </html>
    """

@app.post("/users")
def criar_usuario(user: Usuario):
    usuarios[user.nome] = user
    return {"status": "sucesso"}

@app.get("/login", response_class=HTMLResponse)
def pagina_login():
    return """
    <html>
        <body>
            <h1>Login</h1>
            <form action="/login" method="post">
                <input name="username" placeholder="Usuário">
                <input name="password" type="password" placeholder="Senha">
                <button type="submit">Entrar</button>
            </form>
        </body>
    </html>
    """

@app.post("/login")
def processar_login(response: Response, username: str = Form(...), password: str = Form(...)):
    user = usuarios.get(username)
    if user and user.senha == password:
        response.set_cookie(key="session_id", value=username)
        return {"message": "Login realizado! Vá para /home"}
    return {"message": "Credenciais inválidas"}

@app.get("/home", response_class=HTMLResponse)
def pagina_perfil(user: Usuario = Depends(obter_usuario_logado)):
    return f"""
    <html>
        <body>
            <h1>Bem-vindo, {user.nome}</h1>
            <p><strong>Sua Bio:</strong> {user.bio}</p>
            <a href="/login">Sair (Fazer login com outro)</a>
        </body>
    </html>
    """