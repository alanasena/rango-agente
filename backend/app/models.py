"""Tabelas do banco.

Decisão técnica: todo valor em dinheiro é guardado em CENTAVOS (número inteiro).
Ex.: R$ 32,90 vira 3290. Isso evita erros de arredondamento de números com vírgula
(em Python, 0.1 + 0.2 dá 0.30000000000000004).
"""

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Restaurante(Base):
    __tablename__ = "restaurantes"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100))
    tipo_cozinha: Mapped[str] = mapped_column(String(50))  # ex.: "vegetariana", "pizza"
    nota: Mapped[float] = mapped_column(Float)  # de 0 a 5
    tempo_entrega_min: Mapped[int] = mapped_column(Integer)  # em minutos
    frete_centavos: Mapped[int] = mapped_column(Integer)
    aberto: Mapped[bool] = mapped_column(Boolean, default=True)

    pratos: Mapped[list["Prato"]] = relationship(back_populates="restaurante")


class Prato(Base):
    __tablename__ = "pratos"

    id: Mapped[int] = mapped_column(primary_key=True)
    restaurante_id: Mapped[int] = mapped_column(ForeignKey("restaurantes.id"))
    nome: Mapped[str] = mapped_column(String(100))
    descricao: Mapped[str] = mapped_column(String(255))
    preco_centavos: Mapped[int] = mapped_column(Integer)
    vegetariano: Mapped[bool] = mapped_column(Boolean, default=False)
    vegano: Mapped[bool] = mapped_column(Boolean, default=False)
    disponivel: Mapped[bool] = mapped_column(Boolean, default=True)

    restaurante: Mapped[Restaurante] = relationship(back_populates="pratos")


class Cupom(Base):
    __tablename__ = "cupons"

    codigo: Mapped[str] = mapped_column(String(30), primary_key=True)
    tipo: Mapped[str] = mapped_column(String(20))  # "percentual", "fixo" ou "frete_gratis"
    valor: Mapped[int] = mapped_column(Integer)  # % se percentual, centavos se fixo
    pedido_minimo_centavos: Mapped[int] = mapped_column(Integer, default=0)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)


class Pedido(Base):
    __tablename__ = "pedidos"

    id: Mapped[int] = mapped_column(primary_key=True)
    restaurante_id: Mapped[int] = mapped_column(ForeignKey("restaurantes.id"))
    itens: Mapped[list] = mapped_column(JSON)  # [{"prato_id": 1, "quantidade": 2}, ...]
    cupom: Mapped[str | None] = mapped_column(String(30), nullable=True)
    total_centavos: Mapped[int] = mapped_column(Integer)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
