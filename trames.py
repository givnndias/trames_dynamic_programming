import json
import math
from functools import lru_cache


def numero_valido(valor):
    return (
        isinstance(valor, (int, float))
        and not isinstance(valor, bool)
        and math.isfinite(valor)
    )


def carregar_dados(arquivo):
    with open(arquivo, encoding="utf-8") as f:
        dados = json.load(f)

    if not isinstance(dados, list):
        raise ValueError("O JSON deve conter uma lista de trechos.")

    validos = []
    ids = set()

    for trecho in dados:
        try:
            identificadores = ("id_trecho", "origem_id", "destino_id")

            for campo in identificadores:
                valor = trecho[campo]
                if type(valor) is not int or valor <= 0:
                    raise ValueError(f"{campo} inválido")

            distancia = trecho["distancia_m"]
            custo = trecho["custo_recomendacao"]

            if not numero_valido(distancia) or distancia <= 0:
                raise ValueError("distância deve ser maior que zero")

            if not numero_valido(custo) or custo < 0:
                raise ValueError("custo inválido")

            for campo in (
                "IAR",
                "score_recursos",
                "score_seguranca",
                "score_avaliacao",
            ):
                valor = trecho[campo]
                if not numero_valido(valor) or not 0 <= valor <= 100:
                    raise ValueError(f"{campo} fora do intervalo de 0 a 100")

            if trecho["id_trecho"] in ids:
                raise ValueError("ID de trecho repetido")

            ids.add(trecho["id_trecho"])
            validos.append(trecho)

        except (KeyError, TypeError, ValueError) as erro:
            print(f"Registro ignorado: {erro}")

    return validos


def buscar_rotas(trechos, origem, destino, bloqueados=None):
    bloqueados = set(bloqueados or [])
    grafo = {}
    por_id = {}
    nos = set()

    for trecho in trechos:
        nos.update((trecho["origem_id"], trecho["destino_id"]))

        if trecho["id_trecho"] in bloqueados:
            continue

        grafo.setdefault(trecho["origem_id"], []).append(trecho)
        por_id[trecho["id_trecho"]] = trecho

    if origem not in nos or destino not in nos:
        raise ValueError("Origem ou destino não existe na base.")

    if origem == destino:
        return []

    @lru_cache(maxsize=None)
    def resolver(atual, visitados):
        # Caso base: o destino foi alcançado.
        if atual == destino:
            return ((0, ()),)

        candidatos = []

        for trecho in grafo.get(atual, []):
            proximo = trecho["destino_id"]

            # Evita ciclos no percurso.
            if proximo in visitados:
                continue

            restantes = resolver(
                proximo,
                visitados | frozenset([proximo])
            )

            for custo_restante, caminho in restantes:
                custo = trecho["custo_recomendacao"] + custo_restante
                ids = (trecho["id_trecho"],) + caminho
                candidatos.append((custo, ids))

        # Classifica pelo custo e usa os IDs para desempatar.
        candidatos.sort(key=lambda rota: (rota[0], rota[1]))
        return tuple(candidatos[:3])

    caminhos = resolver(origem, frozenset([origem]))
    resultados = []

    for custo, ids in caminhos:
        percurso = [por_id[id_trecho] for id_trecho in ids]
        distancia = sum(t["distancia_m"] for t in percurso)

        def media_ponderada(campo):
            return sum(
                t[campo] * t["distancia_m"] for t in percurso
            ) / distancia

        resultados.append({
            "nos": [origem] + [t["destino_id"] for t in percurso],
            "trechos": list(ids),
            "distancia_m": distancia,
            "custo": round(custo, 2),
            "IAR": round(media_ponderada("IAR"), 2),
            "score_recursos": round(
                media_ponderada("score_recursos"), 2
            ),
            "score_seguranca": round(
                media_ponderada("score_seguranca"), 2
            ),
            "score_avaliacao": round(
                media_ponderada("score_avaliacao"), 2
            ),
        })

    return resultados


def recalcular_rotas(trechos, local_atual, destino, bloqueados):
    return buscar_rotas(trechos, local_atual, destino, bloqueados)


def mostrar_rotas(rotas):
    if not rotas:
        print("Nenhuma rota disponível ou deslocamento desnecessário.")
        return

    for posicao, rota in enumerate(rotas, start=1):
        print(f"\n{posicao}ª opção")
        print("Nós:", rota["nos"])
        print("Trechos:", rota["trechos"])
        print("Distância:", rota["distancia_m"], "metros")
        print("Custo:", rota["custo"])
        print("IAR:", rota["IAR"])
        print("Score de recursos:", rota["score_recursos"])
        print("Score de segurança:", rota["score_seguranca"])


if __name__ == "__main__":
    trechos = carregar_dados("trames_base_integracao.json")

    print("BUSCA INICIAL")
    rotas = buscar_rotas(trechos, origem=1, destino=5)
    mostrar_rotas(rotas)

    if rotas:
        # Simula o bloqueio do primeiro trecho da rota recomendada.
        trecho_bloqueado = rotas[0]["trechos"][0]

        print(f"\nRECÁLCULO: trecho {trecho_bloqueado} bloqueado")
        novas_rotas = recalcular_rotas(
            trechos,
            local_atual=1,
            destino=5,
            bloqueados=[trecho_bloqueado]
        )
        mostrar_rotas(novas_rotas)