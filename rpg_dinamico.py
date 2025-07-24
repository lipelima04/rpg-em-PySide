# -*- coding: utf-8 -*-
import os
import random
import time
import math

# --- CONSTANTES DE CONFIGURAÇÃO DO JOGO ---
XP_PARA_NIVEL = {
    1: 10, 2: 25, 3: 50, 4: 80, 5: 120, 6: 170, 7: 230, 8: 300, 9: 380, 10: float('inf')
}
PONTOS_DISTRIBUICAO_INICIAL = 50
PONTOS_POR_NIVEL = 5
PENALIDADE_XP_DERROTA = 0.30 # 30% de perda de XP ao ser derrotado
PENALIDADE_XP_FUGA = 0.10 # 10% de perda de XP ao fugir
CHANCE_QUEBRA_AO_FUGIR = 0.25
MAX_POCOES_INVENTARIO = 5
MAX_NIVEL = 10


RARIDADES = {
    "comum": {"chance": 0.75, "multiplicador": 1.0, "cor": "\033[97m"},
    "incomum": {"chance": 0.20, "multiplicador": 1.5, "cor": "\033[92m"},
    "raro": {"chance": 0.05, "multiplicador": 2.5, "cor": "\033[94m"}
}
COR_RESET = "\033[0m"

# --- HABILIDADES E CLASSES (ATUALIZADO COM CRÍTICO E ARMAS) ---
CLASSES_BASE = {
    "Feral": {
        "desc": "Usa o Caos para fortalecer seus ataques físicos.",
        "stats": {"vida_base": 50, "forca_base": 15, "defesa_base": 10, "agilidade_base": 10, "caos_base": 40},
        "chance_critico_base": 0.10, # 10%
        "multiplicador_critico_base": 1.1, # Dano normal + 60% (50% base + 10% bônus de classe)
        "armas_permitidas": ["Machado", "Espada Longa"],
        "habilidades": [
            {"nome": "Impacto do Caos", "tipo": "dano", "custo": 8, "multiplicador": 1.35, "desc": "Ataque mágico de dano direto."},
            {"nome": "Frenesi", "tipo": "buff_self", "custo": 10, "atributo": "forca", "valor": 5, "duracao": 3, "desc": "Aumenta a própria força por 3 turnos."}
        ]
    },
    "Sombra": {
        "desc": "Usa o Caos para golpes rápidos e eficientes.",
        "stats": {"vida_base": 60, "forca_base": 10, "defesa_base": 5, "agilidade_base": 15, "caos_base": 40},
        "chance_critico_base": 0.10, # 10%
        "multiplicador_critico_base": 1.1, # Dano normal + 60%
        "armas_permitidas": ["Adaga", "Kama"],
        "habilidades": [
            {"nome": "Lâmina do Caos", "tipo": "dano", "custo": 4, "multiplicador": 1.20, "desc": "Ataque mágico de dano direto."},
            {"nome": "Névoa Tóxica", "tipo": "debuff_enemy", "custo": 7, "efeito": "veneno", "dano_por_turno": 5, "duracao": 3, "desc": "Envenena o alvo, causando dano por 3 turnos."}
        ]
    },
    "Moldador de Essência": {
        "desc": "Transforma sua força vital em poder mágico devastador.",
        "stats": {"vida_base": 45, "forca_base": 20, "defesa_base": 10, "agilidade_base": 10, "caos_base": 60},
        "chance_critico_base": 0.10, # 10%
        "multiplicador_critico_base": 1.1, # Dano normal + 60%
        "armas_permitidas": ["Cajado", "Livro"],
        "habilidades": [
            {"nome": "Orbe do Caos", "tipo": "dano", "custo": 12, "multiplicador": 1.50, "desc": "Ataque mágico de dano direto."},
            {"nome": "Barreira de Caos", "tipo": "buff_self", "custo": 9, "atributo": "defesa", "valor": 7, "duracao": 3, "desc": "Aumenta a própria defesa por 3 turnos."}
        ]
    }
}

# --- EQUIPAMENTOS (ATUALIZADO COM ARMAS DE CLASSE) ---
NOMES_EQUIPAMENTOS = {
    "arma": {
        "Machado": ["de Guerra", "do Carrasco", "Farpado"],
        "Espada Longa": ["de Aço", "Real", "Larga"],
        "Adaga": ["Misericórdia", "Sombria", "Envenenada"],
        "Kama": ["Afiada", "Dupla", "Ritualística"],
        "Cajado": ["do Aprendiz", "Nodoso", "de Cristal"],
        "Livro": ["de Feitiços", "Tomo Proibido", "Grimório Antigo"]
    },
    "capacete": {"prefixos": ["Elmo", "Capacete"], "sufixos": ["da Guarda", "Sombrio"]},
    "armadura": {"prefixos": ["Peitoral", "Cota de Malha"], "sufixos": ["de Placas", "Leve"]},
    "calca": {"prefixos": ["Grevas", "Calças"], "sufixos": ["de Batalha", "do Viajante"]},
    "bota": {"prefixos": ["Botas", "Coturno"], "sufixos": ["de Corrida", "Pesadas"]}
}

INIMIGO_TEMPLATES = { "Goblin Ladrão": {"vida": 20, "forca": 5, "defesa": 2, "agilidade": 8, "caos": 10}, "Orc Guerreiro": {"vida": 40, "forca": 10, "defesa": 5, "agilidade": 3, "caos": 5}, "Lobo das Neves": {"vida": 30, "forca": 8, "defesa": 3, "agilidade": 12, "caos": 15}, "Golem de Pedra": {"vida": 60, "forca": 12, "defesa": 10, "agilidade": 1, "caos": 0}, "Mago Esqueleto": {"vida": 25, "forca": 15, "defesa": 2, "agilidade": 6, "caos": 30} }
CHEFE_TEMPLATES = { "Lich Tirano": {"vida": 150, "forca": 20, "defesa": 15, "agilidade": 10, "caos": 100}, "Behemoth Colossal": {"vida": 250, "forca": 30, "defesa": 25, "agilidade": 5, "caos": 20}, "Quimera Mutante": {"vida": 180, "forca": 25, "defesa": 10, "agilidade": 20, "caos": 50} }
POCA_TEMPLATES = { "cura": {"nome": "Poção de Cura", "valor": 50}, "buff_forca": {"nome": "Elixir de Força", "valor": 5, "duracao": 3}, "buff_defesa": {"nome": "Poção Casca de Ferro", "valor": 5, "duracao": 3}, "buff_agilidade": {"nome": "Extrato de Agilidade", "valor": 5, "duracao": 3} }

# --- CLASSES BASE (A ESTRUTURA DO JOGO) ---

class Item:
    def __init__(self, nome, raridade): self.nome = nome; self.raridade = raridade
    def nome_formatado(self): cor = RARIDADES[self.raridade]['cor']; icone = "✨" if self.raridade == "raro" else ""; return f"{cor}{self.nome} [{self.raridade.capitalize()}] {icone}{COR_RESET}"

class Equipamento(Item):
    def __init__(self, nome, slot, raridade, bonus_vida=0.0, bonus_forca=0.0, bonus_defesa=0.0, bonus_agilidade=0.0, bonus_caos=0.0, bonus_chance_critico=0.0, bonus_dano_critico=0.0):
        super().__init__(nome, raridade)
        self.slot = slot
        self.bonus_vida = float(bonus_vida)
        self.bonus_forca = float(bonus_forca)
        self.bonus_defesa = float(bonus_defesa)
        self.bonus_agilidade = float(bonus_agilidade)
        self.bonus_caos = float(bonus_caos)
        self.bonus_chance_critico = float(bonus_chance_critico)
        self.bonus_dano_critico = float(bonus_dano_critico)
    
    def get_bonus_texto(self):
        bonus = [f"{b:+.1f} {s}" for s,b in [("VIDA",self.bonus_vida), ("CAOS", self.bonus_caos), ("FOR",self.bonus_forca), ("DEF",self.bonus_defesa), ("AGI",self.bonus_agilidade)] if b]
        if self.bonus_chance_critico > 0:
            bonus.append(f"+{self.bonus_chance_critico:.1%} Chance Crítico")
        if self.bonus_dano_critico > 0:
            bonus.append(f"+{self.bonus_dano_critico:.0%} Dano Crítico")
        return f"({', '.join(bonus)})"

    def __str__(self):
        return f"{self.nome_formatado()} {self.get_bonus_texto()}"

class Pocao(Item):
    def __init__(self, nome, raridade, tipo, valor, duracao=0):
        super().__init__(nome, raridade); self.tipo = tipo; self.valor = float(valor); self.duracao = duracao
    def __str__(self):
        if self.tipo == 'cura': return f"{self.nome_formatado()} (Cura {self.valor:.1f} de Vida)"
        else: tipo_str = self.tipo.split('_')[1].upper(); return f"{self.nome_formatado()} (+{self.valor:.1f} {tipo_str} por {self.duracao} turnos)"

class Personagem:
    def __init__(self, nome, vida_base, forca_base, defesa_base, agilidade_base, caos_base, nivel=1):
        self.nome = nome; self.vida_base = float(vida_base); self.forca_base = float(forca_base); self.defesa_base = float(defesa_base); self.agilidade_base = float(agilidade_base); self.caos_base = float(caos_base); self.nivel = nivel
        self.vida_atual = self.vida_base; self.caos_atual = self.caos_base
        self.equipamentos = {"arma": None, "capacete": None, "armadura": None, "calca": None, "bota": None}
        self.buffs_ativos = {}
        self.debuffs_ativos = {}

    @property
    def forca(self): return self.forca_base + sum(eq.bonus_forca for eq in self.equipamentos.values() if eq) + self.buffs_ativos.get('forca', {'valor': 0})['valor']
    @property
    def defesa(self): return self.defesa_base + sum(eq.bonus_defesa for eq in self.equipamentos.values() if eq) + self.buffs_ativos.get('defesa', {'valor': 0})['valor']
    @property
    def agilidade(self): return self.agilidade_base + sum(eq.bonus_agilidade for eq in self.equipamentos.values() if eq) + self.buffs_ativos.get('agilidade', {'valor': 0})['valor']
    @property
    def vida_maxima(self): return self.vida_base + sum(eq.bonus_vida for eq in self.equipamentos.values() if eq)
    @property
    def caos_maximo(self): return self.caos_base + sum(eq.bonus_caos for eq in self.equipamentos.values() if eq)

    def atacar(self, alvo, logger=print):
        logger(f"\n💥 {self.nome} usa um Ataque Básico contra {alvo.nome}!")
        time.sleep(1)
        chance_acerto = max(20, min(100, 90 - (alvo.agilidade - self.agilidade)))
        if random.randint(1, 100) > chance_acerto:
            logger("   💨 ERROU!")
            time.sleep(1)
            return

        is_crit = False
        if hasattr(self, 'chance_critico_total') and random.random() < self.chance_critico_total:
            is_crit = True

        reducao_de_dano = alvo.defesa * 0.3
        dano = max(1.0, self.forca - reducao_de_dano)

        if is_crit:
            dano *= self.dano_critico_total
            logger(f"   >>> 💥 ACERTO CRÍTICO! <<<")
        
        logger(f"   🎯 Acertou! Dano Físico causado: {dano:.1f}!")
        alvo.receber_dano(dano)
        time.sleep(1)

    def receber_dano(self, dano): self.vida_atual -= dano; self.vida_atual = max(0.0, self.vida_atual)
    def esta_vivo(self): return self.vida_atual > 0

    def processar_debuffs(self):
        for efeito, data in list(self.debuffs_ativos.items()):
            if efeito == 'veneno':
                dano_veneno = data['dano_por_turno']
                print(f"🩸 {self.nome} sofre {dano_veneno:.1f} de dano de veneno.")
                self.receber_dano(dano_veneno)
            
            data['turnos_restantes'] -= 1
            if data['turnos_restantes'] <= 0:
                print(f"O efeito do debuff de {efeito.capitalize()} em {self.nome} acabou.")
                del self.debuffs_ativos[efeito]
                time.sleep(1)

    def mostrar_status(self):
        classe_info = f"- O {self.classe.capitalize()} " if hasattr(self, 'classe') else ""
        print(f"--- STATUS: {self.nome} {classe_info}(Nível {self.nivel}) ---")
        print(f"❤️  Vida: {self.vida_atual:.1f} / {self.vida_maxima:.1f}  |  🔮 Caos: {self.caos_atual:.1f} / {self.caos_maximo:.1f}")
        print(f"💪 Força: {self.forca:.1f} | 🛡️ Defesa: {self.defesa:.1f} | 👟 Agilidade: {self.agilidade:.1f}")
        if hasattr(self, 'chance_critico_total'):
            print(f"💥 Chance de Crítico: {self.chance_critico_total:.1%} | 💥 Dano Crítico: {self.dano_critico_total:.0%}")
        if self.buffs_ativos:
            buff_str = ", ".join([f"{data['valor']:.1f} {tipo.upper()} ({data['turnos_restantes']}t)" for tipo, data in self.buffs_ativos.items()])
            print(f"   BUFFS ATIVOS: {buff_str}")
        if self.debuffs_ativos:
            debuff_str = ", ".join([f"{tipo.capitalize()} ({data['turnos_restantes']}t)" for tipo, data in self.debuffs_ativos.items()])
            print(f"   DEBUFFS ATIVOS: {debuff_str}")
    
    def get_battle_stats_texto(self):
        stats = [
            f"❤️ Vida: {self.vida_atual:.1f} / {self.vida_maxima:.1f}",
            f"🔮 Caos: {self.caos_atual:.1f} / {self.caos_maximo:.1f}",
            f"💪 Força: {self.forca:.1f}",
            f"🛡️ Defesa: {self.defesa:.1f}",
            f"👟 Agilidade: {self.agilidade:.1f}"
        ]
        if hasattr(self, 'chance_critico_total'):
            stats.append(f"💥 Crítico: {self.chance_critico_total:.1%} / x{self.dano_critico_total:.2f}")

        if hasattr(self, 'buffs_ativos') and self.buffs_ativos:
            buff_str = ", ".join([f"{data['valor']:.1f} {tipo.upper()} ({data['turnos_restantes']}t)" for tipo, data in self.buffs_ativos.items()])
            stats.append(f"BUFFS: {buff_str}")
        if hasattr(self, 'debuffs_ativos') and self.debuffs_ativos:
            debuff_str = ", ".join([f"{tipo.capitalize()} ({data['turnos_restantes']}t)" for tipo, data in self.debuffs_ativos.items()])
            stats.append(f"DEBUFFS: {debuff_str}")
        return "\n".join(stats)

class Chefao(Personagem):
    def __init__(self, nome, vida_base, forca_base, defesa_base, agilidade_base, caos_base, nivel=1):
        super().__init__(nome, vida_base, forca_base, defesa_base, agilidade_base, caos_base, nivel)
        self.nome = f"🔥 {nome} 🔥"

class Heroi(Personagem):
    def __init__(self, nome, classe, vida_base, forca_base, defesa_base, agilidade_base, caos_base):
        super().__init__(nome, vida_base, forca_base, defesa_base, agilidade_base, caos_base, nivel=1)
        self.classe = classe
        self.xp_atual = 0
        self.xp_proximo_nivel = XP_PARA_NIVEL[self.nivel]
        self.inventario_pocoes = []
        self.proficiencia = 0.0
        self.pontos_distribuidos_por_nivel = {}
    
    @property
    def chance_critico_total(self):
        bonus_arma = self.equipamentos["arma"].bonus_chance_critico if self.equipamentos["arma"] else 0.0
        return min(0.30, CLASSES_BASE[self.classe]["chance_critico_base"] + bonus_arma)

    @property
    def dano_critico_total(self):
        bonus_arma = self.equipamentos["arma"].bonus_dano_critico if self.equipamentos["arma"] else 0.0
        return CLASSES_BASE[self.classe]["multiplicador_critico_base"] + bonus_arma

    def ganhar_xp(self, quantidade, logger=print):
        if self.nivel >= MAX_NIVEL: return False
        self.xp_atual += quantidade
        logger(f"✨ Você ganhou {quantidade} de XP! ({self.xp_atual:.0f}/{self.xp_proximo_nivel})")
        
        teve_level_up = False
        while self.xp_atual >= self.xp_proximo_nivel and self.nivel < MAX_NIVEL:
            self.subir_de_nivel(logger)
            teve_level_up = True
        return teve_level_up

    def subir_de_nivel(self, logger):
        xp_excedente = self.xp_atual - self.xp_proximo_nivel
        self.nivel += 1
        self.xp_atual = xp_excedente
        self.xp_proximo_nivel = XP_PARA_NIVEL.get(self.nivel, float('inf'))
        self.proficiencia += 0.05
        self.vida_base += 20 
        self.caos_base += 10
        logger(f"🎉🎉🎉 LEVEL UP! Você alcançou o Nível {self.nivel}! 🎉🎉🎉")
        logger(f"Sua proficiência, vida e caos base aumentaram.")
        self.vida_atual = self.vida_maxima
        self.caos_atual = self.caos_maximo

    def perder_xp(self, porcentagem, logger=print):
        if self.nivel == 1 and self.xp_atual == 0:
            logger("Você está no nível 1 e não pode perder mais XP.")
            return

        xp_total_acumulado = sum(XP_PARA_NIVEL.get(i, 0) for i in range(1, self.nivel)) + self.xp_atual
        xp_a_perder = math.floor(xp_total_acumulado * porcentagem)
        xp_total_acumulado -= xp_a_perder
        
        logger(f"🩸 Você perdeu {xp_a_perder:.0f} de XP total.")

        novo_nivel = 1
        xp_restante = xp_total_acumulado
        niveis_perdidos = 0

        while novo_nivel < MAX_NIVEL and xp_restante >= XP_PARA_NIVEL[novo_nivel]:
            xp_restante -= XP_PARA_NIVEL[novo_nivel]
            novo_nivel += 1
        
        if self.nivel > novo_nivel:
            niveis_perdidos = self.nivel - novo_nivel
            logger(f"📉 Você perdeu {niveis_perdidos} nível(eis)! Agora você é Nível {novo_nivel}.")

            for i in range(niveis_perdidos):
                nivel_revertido = self.nivel - i
                self.proficiencia -= 0.05
                self.vida_base -= 20
                self.caos_base -= 10
                pontos_reverter = self.pontos_distribuidos_por_nivel.pop(nivel_revertido, None)
                if pontos_reverter:
                    self.forca_base -= pontos_reverter.get('forca_base', 0)
                    self.defesa_base -= pontos_reverter.get('defesa_base', 0)
                    self.agilidade_base -= pontos_reverter.get('agilidade_base', 0)
            logger("Seus atributos base foram reduzidos.")

        self.nivel = novo_nivel
        self.xp_atual = xp_restante
        self.xp_proximo_nivel = XP_PARA_NIVEL.get(self.nivel, float('inf'))
            
        self.vida_atual = min(self.vida_atual, self.vida_maxima)
        self.caos_atual = min(self.caos_atual, self.caos_maximo)

    def usar_habilidade(self, habilidade_index, alvo):
        habilidade = CLASSES_BASE[self.classe]['habilidades'][habilidade_index]
        custo = habilidade['custo']
        
        if self.caos_atual < custo:
            print("Caos insuficiente para usar esta habilidade!")
            time.sleep(2)
            return False
            
        self.caos_atual -= custo
        print(f"\n✨ {self.nome} usa {habilidade['nome']}!")
        time.sleep(1)

        tipo_habilidade = habilidade['tipo']
        
        if tipo_habilidade == 'dano':
            multiplicador = habilidade['multiplicador'] + self.proficiencia
            dano_magico = self.forca * multiplicador
            print(f"   Dano Mágico causado: {dano_magico:.1f}! (Ignora defesa)")
            alvo.receber_dano(dano_magico)
        
        elif tipo_habilidade == 'buff_self':
            atributo = habilidade['atributo']
            self.buffs_ativos[atributo] = {'valor': habilidade['valor'], 'turnos_restantes': habilidade['duracao'] + 1}
            print(f"   Seu atributo {atributo.upper()} aumentou em {habilidade['valor']:.1f} por {habilidade['duracao']} turnos!")

        elif tipo_habilidade == 'debuff_enemy':
            efeito = habilidade['efeito']
            alvo.debuffs_ativos[efeito] = {'dano_por_turno': habilidade['dano_por_turno'], 'turnos_restantes': habilidade['duracao'] + 1}
            print(f"   {alvo.nome} foi afetado por {efeito.capitalize()} por {habilidade['duracao']} turnos!")

        time.sleep(1)
        return True

    def usar_pocao(self, pocao_index):
        pocao = self.inventario_pocoes.pop(pocao_index); print(f"\nVocê usou {pocao.nome_formatado()}!")
        if pocao.tipo == 'cura':
            vida_curada = min(self.vida_maxima - self.vida_atual, pocao.valor); self.vida_atual += vida_curada
            print(f"   Você recuperou {vida_curada:.1f} de vida.")
        else:
            tipo_buff = pocao.tipo.split('_')[1]; self.buffs_ativos[tipo_buff] = {'valor': pocao.valor, 'turnos_restantes': pocao.duracao + 1}
            print(f"   Seu atributo {tipo_buff.upper()} aumentou em {pocao.valor:.1f} por {pocao.duracao} turnos!")
        time.sleep(2)

    def processar_buffs(self):
        for tipo, data in list(self.buffs_ativos.items()):
            data['turnos_restantes'] -= 1
            if data['turnos_restantes'] <= 0: print(f"O efeito do buff de {tipo.upper()} acabou."); del self.buffs_ativos[tipo]; time.sleep(1)

    def avaliar_e_equipar_item(self, novo_equip, logger=print):
        item_atual = self.equipamentos[novo_equip.slot]
        bonus_vida_antigo = item_atual.bonus_vida if item_atual else 0.0
        bonus_caos_antigo = item_atual.bonus_caos if item_atual else 0.0
        if item_atual: logger(f"   Substituindo {item_atual.nome_formatado()}...")
        self.equipamentos[novo_equip.slot] = novo_equip
        delta_vida = novo_equip.bonus_vida - bonus_vida_antigo
        delta_caos = novo_equip.bonus_caos - bonus_caos_antigo
        self.vida_atual += delta_vida
        self.caos_atual += delta_caos
        self.vida_atual = min(self.vida_maxima, self.vida_atual)
        self.caos_atual = min(self.caos_maximo, self.caos_atual)
        logger(f"   {self.nome} equipou {novo_equip.nome_formatado()}.")
        return True

    def mostrar_status_completo(self):
        super().mostrar_status()
        if self.nivel < MAX_NIVEL: print(f"📊 XP: {self.xp_atual:.0f} / {self.xp_proximo_nivel}")
        else: print("📊 XP: MÁXIMO")
        print("--- Atributos Base ---"); print(f"   - Vida: {self.vida_base:.1f}, Força: {self.forca_base:.1f}, Defesa: {self.defesa_base:.1f}, Agilidade: {self.agilidade_base:.1f}, Caos: {self.caos_base:.1f}")
        print("--- Equipamentos ---"); [print(f"   - {slot.capitalize()}: {item if item else 'Vazio'}") for slot, item in self.equipamentos.items()]
        print("--- Inventário de Poções ---");
        if self.inventario_pocoes: [print(f"   - {pocao}") for pocao in self.inventario_pocoes]
        else: print("   Vazio")
        print("--------------------")

# --- BANCO DE DADOS E FUNÇÕES GLOBAIS ---
HEROIS_CRIADOS = {}
def limpar_tela(): os.system('cls' if os.name == 'nt' else 'clear')
def obter_raridade():
    roll = random.random(); cumulative_chance = 0
    for raridade in ["comum", "incomum", "raro"]:
        data = RARIDADES[raridade]
        cumulative_chance += data['chance'];
        if roll < cumulative_chance: return raridade
    return "comum"

def gerar_inimigo(nivel_heroi):
    nome_template = random.choice(list(INIMIGO_TEMPLATES.keys())); stats_base = INIMIGO_TEMPLATES[nome_template]
    pontos_extras = (nivel_heroi - 1) * 8
    vida_final = stats_base["vida"] + pontos_extras * 2; forca_final = stats_base["forca"] + pontos_extras * 0.5; defesa_final = stats_base["defesa"] + pontos_extras * 0.3; agilidade_final = stats_base["agilidade"] + pontos_extras * 0.2; caos_final = stats_base["caos"]
    return Personagem(f"{nome_template} (N{nivel_heroi})", vida_final, forca_final, defesa_final, agilidade_final, caos_final, nivel=nivel_heroi)

def gerar_chefe(nivel_heroi):
    nome_template = random.choice(list(CHEFE_TEMPLATES.keys())); stats_base = CHEFE_TEMPLATES[nome_template]
    pontos_extras = (nivel_heroi - 1) * 12
    vida_final = stats_base["vida"] + pontos_extras * 4; forca_final = stats_base["forca"] + pontos_extras * 0.6; defesa_final = stats_base["defesa"] + pontos_extras * 0.4; agilidade_final = stats_base["agilidade"] + pontos_extras * 0.2; caos_final = stats_base["caos"]
    return Chefao(f"{nome_template} (N{nivel_heroi})", vida_final, forca_final, defesa_final, agilidade_final, caos_final, nivel=nivel_heroi)

def gerar_recompensa_aleatoria(heroi):
    if random.random() > 0.4: # Gerar Equipamento
        slot = random.choice(list(NOMES_EQUIPAMENTOS.keys()))
        raridade = obter_raridade()
        multiplicador = RARIDADES[raridade]['multiplicador']
        bonus_base = heroi.nivel * 2

        if slot == "arma":
            armas_permitidas = CLASSES_BASE[heroi.classe]["armas_permitidas"]
            tipo_arma = random.choice(armas_permitidas)
            sufixo = random.choice(NOMES_EQUIPAMENTOS["arma"][tipo_arma])
            nome_item = f"{tipo_arma} {sufixo}"

            if raridade == "comum":
                chance_crit = random.uniform(0.05, 0.10)
                dano_crit = random.uniform(0.15, 0.40)
            elif raridade == "incomum":
                chance_crit = random.uniform(0.11, 0.15)
                dano_crit = random.uniform(0.40, 0.65)
            else: # Raro
                chance_crit = random.uniform(0.16, 0.20)
                dano_crit = random.uniform(0.65, 0.90)

            return Equipamento(nome_item, slot, raridade,
                               bonus_forca=random.uniform(bonus_base, bonus_base + 3) * multiplicador,
                               bonus_chance_critico=chance_crit,
                               bonus_dano_critico=dano_crit)
        else:
            prefixo = random.choice(NOMES_EQUIPAMENTOS[slot]["prefixos"])
            sufixo = random.choice(NOMES_EQUIPAMENTOS[slot]["sufixos"])
            nome_item = f"{prefixo} {sufixo}"
            bonus_caos = (random.uniform(bonus_base, bonus_base + 2) * multiplicador) if random.random() < 0.2 else 0
            
            if slot == "capacete": return Equipamento(nome_item, slot, raridade, bonus_defesa=random.uniform(bonus_base, bonus_base + 2) * multiplicador, bonus_agilidade=-random.uniform(1, 2), bonus_caos=bonus_caos)
            if slot == "armadura": return Equipamento(nome_item, slot, raridade, bonus_defesa=random.uniform(bonus_base, bonus_base + 5) * multiplicador, bonus_vida=bonus_base*2*multiplicador)
            if slot == "calca": return Equipamento(nome_item, slot, raridade, bonus_agilidade=random.uniform(bonus_base, bonus_base + 2) * multiplicador, bonus_vida=bonus_base*multiplicador)
            if slot == "bota": return Equipamento(nome_item, slot, raridade, bonus_agilidade=random.uniform(bonus_base, bonus_base + 2) * multiplicador, bonus_defesa=-random.uniform(1, 2))

    else: # Gerar Poção
        raridade = obter_raridade()
        multiplicador = RARIDADES[raridade]['multiplicador']
        tipo_pocao = random.choice(list(POCA_TEMPLATES.keys()))
        template = POCA_TEMPLATES[tipo_pocao]
        valor_final = template.get('valor', 0) * multiplicador
        return Pocao(template['nome'], raridade, tipo_pocao, valor_final, template.get('duracao', 0))

# --- TELAS E MENUS DO JOGO (MODO TEXTO) ---
# O resto das funções do modo texto permanecem para referência, mas não são usadas pela GUI.
