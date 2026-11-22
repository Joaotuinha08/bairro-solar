"""Fila op.aviso: escreve o aviso aos membros na consola (ARCHITECTURE 5.6)."""


def mensagem(evento: dict) -> str:
    d = evento["dados"]
    if evento["tipo"] == "excedente.iniciado":
        return f"[AVISO] Excedente iniciado no periodo {d['periodo']} (saldo {d['saldo_kw']:+.1f} kW). Aproveite a energia!"
    if evento["tipo"] == "excedente.terminado":
        return f"[AVISO] Excedente terminado no periodo {d['periodo']} (saldo {d['saldo_kw']:+.1f} kW)."
    raise ValueError(f"op.aviso não trata eventos do tipo {evento['tipo']!r}")


def tratar(conn, evento: dict) -> None:  # noqa: ARG001 - o aviso não guarda nada
    print(mensagem(evento), flush=True)
