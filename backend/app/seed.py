"""Preenche o banco com dados FICTÍCIOS do Rangô.

Todos os restaurantes, pratos, preços, fretes e cupons são inventados
e ficam em app/dados_ficticios.py.
Rodar de novo apaga tudo e recria do zero (bom para testes).

Como rodar (dentro da pasta backend):
    python -m app.seed
"""

from app.database import Base, SessionLocal, engine
from app.models import Cupom, Prato, Restaurante

from app.dados_ficticios import CUPONS, RESTAURANTES  # os dados ficam neste outro arquivo


def popular_banco() -> None:
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    with SessionLocal() as db:
        for nome, tipo, nota, tempo, frete, aberto, pratos in RESTAURANTES:
            restaurante = Restaurante(
                nome=nome,
                tipo_cozinha=tipo,
                nota=nota,
                tempo_entrega_min=tempo,
                frete_centavos=frete,
                aberto=aberto,
            )
            for p_nome, desc, preco, veg, vegano in pratos:
                restaurante.pratos.append(
                    Prato(
                        nome=p_nome,
                        descricao=desc,
                        preco_centavos=preco,
                        vegetariano=veg,
                        vegano=vegano,
                    )
                )
            db.add(restaurante)

        for codigo, tipo, valor, minimo, ativo in CUPONS:
            db.add(Cupom(codigo=codigo, tipo=tipo, valor=valor,
                         pedido_minimo_centavos=minimo, ativo=ativo))

        db.commit()

        total_rest = db.query(Restaurante).count()
        total_pratos = db.query(Prato).count()
        total_cupons = db.query(Cupom).count()

    print(f"Banco pronto: {total_rest} restaurantes, {total_pratos} pratos, {total_cupons} cupons.")


if __name__ == "__main__":
    popular_banco()
