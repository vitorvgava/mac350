from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship

class Autor(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nome: str

    livros: List["Livro"] = Relationship(
        back_populates="autor",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

class Livro(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    titulo: str = Field(min_length=1)
    avaliacao: int = Field(ge=0, le=5)
    autor_id: int = Field(foreign_key="autor.id")

    autor: Optional[Autor] = Relationship(back_populates="livros")