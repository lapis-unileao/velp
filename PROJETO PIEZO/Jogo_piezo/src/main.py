import pygame
import sys
import time
import random
import math
from serial_thread import SerialReader
import os
BASE_DIR = os.path.dirname(__file__)


# =======================
# CONFIGURAÇÕES INICIAIS
# =======================
pygame.init()
LARGURA, ALTURA = 1280, 720
TELA = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Velp - Treino de Força Pélvica")
# === FUNDO DO JOGO ===
fundo_img = pygame.image.load(os.path.join(BASE_DIR, "imagens", "fundo.png")).convert()
fundo_img = pygame.transform.scale(fundo_img, (LARGURA, ALTURA))
# === IMAGENS DOS OBSTÁCULOS (carregadas com escala controlada) ===
def load_obst_img(filename, target_h):
    """Carrega a imagem e escala a altura para target_h mantendo proporção."""
    img = pygame.image.load(os.path.join(BASE_DIR, "imagens", filename)).convert_alpha()
    w, h = img.get_size()
    if h == 0:
        return img
    scale = target_h / h
    return pygame.transform.smoothscale(img, (int(w * scale), int(h * scale)))

# Ajuste target_h conforme preferir (valores em pixels)
img_cacto = load_obst_img("cacto.png", target_h=130)
img_pedra = load_obst_img("pedra.png", target_h=130)
img_arbusto = load_obst_img("arbusto.png", target_h=130)
obstaculo_imgs = [img_cacto, img_pedra, img_arbusto]

# ==================== PERSONAGEM ====================

# Frames de corrida
personagem_correndo = [
    pygame.image.load(os.path.join(BASE_DIR, "imagens", "c1.png")).convert_alpha(),
    pygame.image.load(os.path.join(BASE_DIR, "imagens", "c2.png")).convert_alpha(),
    pygame.image.load(os.path.join(BASE_DIR, "imagens", "c3.png")).convert_alpha(),
    pygame.image.load(os.path.join(BASE_DIR, "imagens", "c4.png")).convert_alpha(),
]

# Sequência EXATA do pulo (como você pediu e desenhou no relatório!)
frames_pulo = [
    pygame.image.load(os.path.join(BASE_DIR, "imagens", "p1.png")).convert_alpha(),  # preparação no chão
    pygame.image.load(os.path.join(BASE_DIR, "imagens", "p2.png")).convert_alpha(),  # preparação no chão
    pygame.image.load(os.path.join(BASE_DIR, "imagens", "p3.png")).convert_alpha(),  # subindo
    pygame.image.load(os.path.join(BASE_DIR, "imagens", "p4.png")).convert_alpha(),  # subindo mais
    pygame.image.load(os.path.join(BASE_DIR, "imagens", "p5.png")).convert_alpha(),  # topo do pulo
    pygame.image.load(os.path.join(BASE_DIR, "imagens", "p3.png")).convert_alpha(),  # começando a descer
    pygame.image.load(os.path.join(BASE_DIR, "imagens", "p2.png")).convert_alpha(),  # descendo
    pygame.image.load(os.path.join(BASE_DIR, "imagens", "p1.png")).convert_alpha(),  # aterrissagem perfeita
]

# Redimensiona tudo (altura 200px)
def scale(img, h=200):
    escala = h / img.get_height()
    return pygame.transform.smoothscale(img, (int(img.get_width() * escala), int(h)))

personagem_correndo = [scale(img) for img in personagem_correndo]
frames_pulo = [scale(img) for img in frames_pulo]

# Controle da animação
frame_corrida = 0
tempo_corrida = 0
intervalo_corrida = 100  # ms por frame

em_pulo = False
pulo_frame = 0
pulo_tempo_inicio = 0
duracao_pulo = 850  # 850ms = animação perfeita (ajuste só se quiser mais rápido/lento)
# Paleta de cores
COR_FUNDO_CEU = (240, 225, 245)
COR_MONTANHAS = (210, 190, 230)
COR_CHAO = (230, 220, 245)
COR_JOGADOR = (180, 140, 220)
COR_OBSTACULO = (200, 150, 220)
COR_TEXTO = (60, 40, 70)
COR_BOTAO = (224, 122, 158)
COR_BOTAO_HOVER = (235, 150, 180)
COR_SOMBRA = (200, 100, 140)

# Fontes
fonte_titulo = pygame.font.SysFont("Poppins", 130, bold=True)
fonte_padrao = pygame.font.SysFont("Poppins", 32)
fonte_pequena = pygame.font.SysFont("Poppins", 22)
# altura do chão (usada tanto no desenho do chão quanto no posicionamento dos obstáculos)
CHAO_HEIGHT = 80


clock = pygame.time.Clock()
FPS = 60

# Estados
ESTADO = "menu"

# Variáveis do jogador
x_jogador = 150
y_jogador = 580
velocidade_y = 0
gravidade = 0.5
pulando = False
forca_lida = 0.0

# Obstáculos
obstaculos = []
velocidade_obstaculos = 7
intervalo_obstaculo = 1500  # milissegundos
ultimo_obstaculo = pygame.time.get_ticks()

# Conexão serial com Arduino
try:
    leitor_serial = SerialReader(port="COM3", baud=9600)
    leitor_serial.start()
except Exception as e:
    print("⚠️ Erro ao conectar com Arduino:", e)
    leitor_serial = None

time.sleep(1.5)

gravidade = 0.8                
DURACAO_PULO_MIN_MS = 700     
DURACAO_PULO_MAX_MS = 1300    
NIVEL_SENSIBILIDADE = "normal"
FATOR_FORCA = {"baixa": 1.4, "normal": 1.0, "alta": 0.7}

velocidade_obstaculos = 6
intervalo_obstaculo = 2000
velocidade_fundo = 1.5

em_pulo = False
pulo_tempo_inicio = 0
duracao_pulo_ms = 800
velocidade_y = 0


# =====================================================================
# ====================== 🎨 DESIGN DO MENU PRINCIPAL 🎨 ======================
# =====================================================================

def desenhar_gradiente_superior_inferior(tela, cor_inicio, cor_fim):
    for y in range(ALTURA):
        proporcao = y / ALTURA
        r = int(cor_inicio[0] * (1 - proporcao) + cor_fim[0] * proporcao)
        g = int(cor_inicio[1] * (1 - proporcao) + cor_fim[1] * proporcao)
        b = int(cor_inicio[2] * (1 - proporcao) + cor_fim[2] * proporcao)
        pygame.draw.line(tela, (r, g, b), (0, y), (LARGURA, y))

# Elementos animados do menu
gotas = [{"x": random.randint(0, LARGURA), "y": random.randint(-700, 0), "vel": random.uniform(2, 4)} for _ in range(35)]
textura_floral = [{"x": random.randint(0, LARGURA), "y": random.randint(0, ALTURA),
                   "raio": random.randint(18, 30)} for _ in range(25)]

def desenhar_fundo_menu():
    desenhar_gradiente_superior_inferior(TELA, (235, 220, 250), (210, 185, 230))

    # Textura floral (fundo sutil)
    for flor in textura_floral:
        superficie = pygame.Surface((flor["raio"]*2, flor["raio"]*2), pygame.SRCALPHA)
        pygame.draw.circle(superficie, (255, 240, 250, 25), (flor["raio"], flor["raio"]), flor["raio"])
        TELA.blit(superficie, (flor["x"], flor["y"]))

    # Gotas de água caindo
    for gota in gotas:
        pygame.draw.ellipse(TELA, (255, 255, 255, 140), (gota["x"], gota["y"], 6, 12))
        gota["y"] += gota["vel"]
        if gota["y"] > ALTURA:
            gota["y"] = random.randint(-60, -10)
            gota["x"] = random.randint(0, LARGURA)

def desenhar_titulo_gradiente(texto):
    fonte_temp = pygame.font.SysFont("Poppins", 160, bold=True)
    superficie_texto = fonte_temp.render(texto, True, (255, 255, 255))
    largura, altura = superficie_texto.get_size()
    degradê = pygame.Surface((largura, altura))
    for y in range(altura):
        proporcao = y / altura
        r = int(224 * (1 - proporcao) + 255 * proporcao)
        g = int(122 * (1 - proporcao) + 182 * proporcao)
        b = int(158 * (1 - proporcao) + 193 * proporcao)
        pygame.draw.line(degradê, (r, g, b), (0, y), (largura, y))
    superficie_texto.blit(degradê, (0, 0), special_flags=pygame.BLEND_MULT)
    return superficie_texto

def desenhar_botao(texto, x, y, largura, altura, cor, cor_hover, acao=None):
    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()
    cor_usada = cor_hover if (x + largura > mouse[0] > x and y + altura > mouse[1] > y) else cor

    sombra_rect = pygame.Rect(x + 4, y + 6, largura, altura)
    pygame.draw.rect(TELA, COR_SOMBRA, sombra_rect, border_radius=20)
    pygame.draw.rect(TELA, cor_usada, (x, y, largura, altura), border_radius=20)

    texto_render = fonte_padrao.render(texto, True, (255, 255, 255))
    TELA.blit(texto_render, (x + largura/2 - texto_render.get_width()/2, y + altura/2 - 15))

    if x + largura > mouse[0] > x and y + altura > mouse[1] > y and click[0] == 1 and acao:
        acao()
        time.sleep(0.2)

# =====================================================================
# ====================== 🎮 DESIGN DA TELA DO JOGO 🎮 ======================
# =====================================================================

# === CONFIGURAÇÃO DO FUNDO ===
fundo = pygame.image.load(os.path.join(os.path.dirname(__file__), "imagens", "fundo.png")).convert()
largura_fundo = fundo.get_width()
x_fundo = 0
velocidade_fundo = 0  # velocidade de rolagem do fundo

def desenhar_fundo():
    """Desenha o fundo do jogo com efeito de movimento e chão integrado."""
    global x_fundo
    largura_fundo = fundo_img.get_width()
    x_rel = x_fundo % largura_fundo

    # Fundo rolando
    TELA.blit(fundo_img, (x_rel - largura_fundo, 0))
    if x_rel < LARGURA:
        TELA.blit(fundo_img, (x_rel, 0))
    x_fundo -= velocidade_fundo

    # Desenhar o chão
    altura_chao = 80
    cor_chao_superior = (90, 50, 120)   # Roxo escuro suave
    cor_chao_inferior = (60, 35, 90)    # Roxo ainda mais escuro (degradê)

    # Cria o degradê do chão
    for i in range(altura_chao):
        proporcao = i / altura_chao
        r = int(cor_chao_superior[0] * (1 - proporcao) + cor_chao_inferior[0] * proporcao)
        g = int(cor_chao_superior[1] * (1 - proporcao) + cor_chao_inferior[1] * proporcao)
        b = int(cor_chao_superior[2] * (1 - proporcao) + cor_chao_inferior[2] * proporcao)
        pygame.draw.line(TELA, (r, g, b), (0, ALTURA - altura_chao + i), (LARGURA, ALTURA - altura_chao + i))

    # Linha de transição entre o fundo e o chão (para suavizar)
    pygame.draw.line(TELA, (110, 70, 150), (0, ALTURA - altura_chao), (LARGURA, ALTURA - altura_chao), 3)


def desenhar_barra_forca(valor):
    largura_max = 400
    x_barra = 50
    y_barra = 670
    proporcao = min(valor / 100.0, 1.0)
    largura_barra = int(largura_max * proporcao)

    pygame.draw.rect(TELA, (220, 200, 230), (x_barra, y_barra, largura_max, 20), border_radius=10)
    pygame.draw.rect(TELA, (160, 100, 200), (x_barra, y_barra, largura_barra, 20), border_radius=10)
    texto = fonte_padrao.render(f"Força: {valor:.1f} N", True, COR_TEXTO)
    TELA.blit(texto, (x_barra + largura_max + 30, y_barra - 3))

# =====================================================================
# ====================== 🔧 ESTADOS E AÇÕES 🔧 ======================
# =====================================================================

def iniciar_jogo():
    global ESTADO, obstaculos, y_jogador, velocidade_y, pulando, forca_maxima_sessao, forca_total, contracoes_efetivas, pontuacao, tempo_inicio, velocidade_obstaculos, intervalo_obstaculo, velocidade_fundo, tempo_sessao_final
    obstaculos = []
    y_jogador = 580
    velocidade_y = 0
    pulando = False
    forca_maxima_sessao = 0
    forca_total = 0
    contracoes_efetivas = 0
    pontuacao = 0
    tempo_inicio = time.time()
    velocidade_obstaculos = 7
    intervalo_obstaculo = 1500
    velocidade_fundo = 2  # Inicia com movimento suave
    tempo_sessao_final = 0
    ESTADO = "jogo"

def sair_jogo():
    if leitor_serial:
        leitor_serial.stop()
    pygame.quit()
    sys.exit()

def abrir_configuracoes():
    global ESTADO
    ESTADO = "configuracoes"

def voltar_menu():
    global ESTADO
    ESTADO = "menu"

# =====================================================================
# ====================== NOVA CURVA SIGMOIDE + NÍVEIS ======================
# =====================================================================
NIVEL_SENSIBILIDADE = "normal"  # "baixa", "normal", "alta"
FATOR_FORCA = {"baixa": 1.4, "normal": 1.0, "alta": 0.7}

def forca_para_pulo(forca):
    fator = FATOR_FORCA.get(NIVEL_SENSIBILIDADE, 1.0)
    x = (forca * fator - 50) / 20.0
    intensidade = 1 / (1 + math.exp(-x))  # 0.0 a 1.0
    return -18 * intensidade  # velocidade_y máxima = -18

# =====================================================================
# ====================== FEEDBACK VISUAL DE FORÇA ======================
# =====================================================================
particulas_forca = []

def criar_particulas_forca(x, y):
    for _ in range(12):
        particulas_forca.append({
            "x": x + 60,
            "y": y + 80,
            "vx": random.uniform(-3, 3),
            "vy": random.uniform(-5, -1),
            "vida": 30,
            "cor": (255, 180, 220)
        })

# =====================================================================
# ====================== TELA DE CONFIGURAÇÕES ======================
# =====================================================================
def desenhar_tela_configuracoes():
    desenhar_fundo_menu()
    
    titulo = desenhar_titulo_gradiente("Configurações")
    TELA.blit(titulo, (LARGURA/2 - titulo.get_width()/2, 100))

    espacamento = 80
    largura_botao = 300
    altura_botao = 60
    x_botao = LARGURA/2 - largura_botao/2
    y_base = 250

    def set_baixa():
        global NIVEL_SENSIBILIDADE
        NIVEL_SENSIBILIDADE = "baixa"
    
    def set_normal():
        global NIVEL_SENSIBILIDADE
        NIVEL_SENSIBILIDADE = "normal"
    
    def set_alta():
        global NIVEL_SENSIBILIDADE
        NIVEL_SENSIBILIDADE = "alta"

    desenhar_botao("Sensibilidade: Baixa", x_botao, y_base, largura_botao, altura_botao, COR_BOTAO, COR_BOTAO_HOVER, set_baixa)
    desenhar_botao("Sensibilidade: Normal", x_botao, y_base + espacamento, largura_botao, altura_botao, COR_BOTAO, COR_BOTAO_HOVER, set_normal)
    desenhar_botao("Sensibilidade: Alta", x_botao, y_base + 2*espacamento, largura_botao, altura_botao, COR_BOTAO, COR_BOTAO_HOVER, set_alta)
    desenhar_botao("Voltar", x_botao, y_base + 3*espacamento + 50, largura_botao, altura_botao, (180, 110, 140), (200, 130, 160), voltar_menu)

    status = fonte_padrao.render(f"Nível atual: {NIVEL_SENSIBILIDADE.capitalize()}", True, COR_TEXTO)
    TELA.blit(status, (LARGURA/2 - status.get_width()/2, 220))

# =====================================================================
# ====================== TELA DE RESULTADOS ======================
# =====================================================================
forca_maxima_sessao = 0
forca_total = 0
contracoes_efetivas = 0
pontuacao = 0
tempo_inicio = 0
tempo_sessao_final = 0

def desenhar_tela_resultados():
    desenhar_fundo_menu()
    
    titulo = desenhar_titulo_gradiente("Resultados")
    TELA.blit(titulo, (LARGURA/2 - titulo.get_width()/2, 100))

    y_base = 250
    espacamento = 40
    
    forca_media = forca_total / max(contracoes_efetivas, 1)
    
    textos = [
        f"Pontuação: {pontuacao}",
        f"Força Máxima: {forca_maxima_sessao:.1f} N",
        f"Força Média: {forca_media:.1f} N",
        f"Contrações Efetivas: {contracoes_efetivas}",
        f"Tempo de Sessão: {tempo_sessao_final:.1f} segundos"
    ]
    
    for i, texto in enumerate(textos):
        render = fonte_padrao.render(texto, True, COR_TEXTO)
        TELA.blit(render, (LARGURA/2 - render.get_width()/2, y_base + i * espacamento))

    largura_botao = 240
    altura_botao = 70
    x_botao = LARGURA/2 - largura_botao/2
    desenhar_botao("Voltar ao Menu", x_botao, y_base + len(textos)*espacamento + 50, largura_botao, altura_botao, COR_BOTAO, COR_BOTAO_HOVER, voltar_menu)

# =====================================================================
# ====================== PROGRESSÃO DE DIFICULDADE ======================
# =====================================================================
ultimo_aumento_dificuldade = 0

# =====================================================================
# ====================== 🔁 LOOP PRINCIPAL 🔁 ======================
# =====================================================================
rodando = True
tempo_total = 0

while rodando:
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            rodando = False

    if ESTADO == "menu":
        tempo_total += clock.get_time() / 1000
        desenhar_fundo_menu()

        titulo = desenhar_titulo_gradiente("VELP")
        deslocamento = math.sin(tempo_total * 2) * 8
        TELA.blit(titulo, (LARGURA/2 - titulo.get_width()/2, 150 + deslocamento))

        subtitulo = fonte_padrao.render("Treino de Força Pélvica", True, COR_TEXTO)
        TELA.blit(subtitulo, (LARGURA/2 - subtitulo.get_width()/2, 290))

        espacamento = 80
        largura_botao = 240
        altura_botao = 70
        x_botao = LARGURA/2 - largura_botao/2
        y_base = 420

        desenhar_botao("Iniciar", x_botao, y_base, largura_botao, altura_botao, COR_BOTAO, COR_BOTAO_HOVER, iniciar_jogo)
        desenhar_botao("Configurações", x_botao, y_base + espacamento, largura_botao, altura_botao, COR_BOTAO, COR_BOTAO_HOVER, abrir_configuracoes)
        desenhar_botao("Sair", x_botao, y_base + 2*espacamento, largura_botao, altura_botao, (180, 110, 140), (200, 130, 160), sair_jogo)

        creditos = fonte_pequena.render("Laboratório LAPIS - Unileão", True, (90, 70, 100))
        TELA.blit(creditos, (LARGURA - creditos.get_width() - 30, ALTURA - 30))

    elif ESTADO == "configuracoes":
        desenhar_tela_configuracoes()

    elif ESTADO == "resultados":
        desenhar_tela_resultados()

    elif ESTADO == "jogo":
        # Fundo
        desenhar_fundo()

        # Leitura do sensor
        if leitor_serial:
            valor = leitor_serial.get_valor()
            if valor is not None:
                forca_lida = max(0, valor)  # Evita negativos

        # Atualiza métricas clínicas
        if forca_lida > forca_maxima_sessao:
            forca_maxima_sessao = forca_lida
        if forca_lida > 20:  # Contração detectada
            forca_total += forca_lida
            if forca_lida > 60:
                contracoes_efetivas += 1

        # Pulo proporcional com sigmoide
        if forca_lida > 20 and not pulando:
            velocidade_y = forca_para_pulo(forca_lida)
            pulando = True
            if forca_lida > 60:
                criar_particulas_forca(x_jogador, y_jogador)

        # Atualiza gravidade
        y_jogador += velocidade_y
        velocidade_y += gravidade
        if y_jogador >= 580:
            y_jogador = 580
            velocidade_y = 0
            pulando = False

        # === OBSTÁCULOS ===
        tempo_atual = pygame.time.get_ticks()
        if tempo_atual - ultimo_obstaculo > intervalo_obstaculo:
            img = random.choice(obstaculo_imgs)
            largura_img, altura_img = img.get_size()
            rect = pygame.Rect(LARGURA, 680 - altura_img, largura_img, altura_img)
            obstaculos.append({"img": img, "rect": rect})
            ultimo_obstaculo = tempo_atual

        # Movimenta e desenha obstáculos
        for obstaculo in obstaculos[:]:
            obstaculo["rect"].x -= velocidade_obstaculos
            if obstaculo["rect"].x + obstaculo["rect"].width < 0:
                obstaculos.remove(obstaculo)
                pontuacao += 10  # Pontos por obstáculo evitado
            else:
                TELA.blit(obstaculo["img"], (obstaculo["rect"].x, obstaculo["rect"].y))

        # Progressão de dificuldade (a cada 15 seg)
        if tempo_atual - ultimo_aumento_dificuldade > 15000:
            velocidade_obstaculos += 0.5
            intervalo_obstaculo = max(800, intervalo_obstaculo - 100)
            velocidade_fundo += 0.2
            ultimo_aumento_dificuldade = tempo_atual

                     # === ANIMAÇÃO DO PERSONAGEM (FINAL E PERFEITA) ===
        tempo_corrida += clock.get_time()

        # Inicia o pulo com força suficiente
        if forca_lida > 20 and not em_pulo and y_jogador >= 580:
            velocidade_y = forca_para_pulo(forca_lida)
            em_pulo = True
            pulo_tempo_inicio = pygame.time.get_ticks()
            pulo_frame = 0
            if forca_lida > 60:
                criar_particulas_forca(x_jogador, y_jogador)

        # Física + animação do pulo
        if em_pulo:
            y_jogador += velocidade_y
            velocidade_y += gravidade

            # Animação baseada no tempo (exatamente p1→p2→p3→p4→p5→p3→p2→p1)
            tempo_no_ar = pygame.time.get_ticks() - pulo_tempo_inicio
            progresso = tempo_no_ar / duracao_pulo
            if progresso > 1.0:
                progresso = 1.0

            pulo_frame = int(progresso * len(frames_pulo))
            if pulo_frame >= len(frames_pulo):
                pulo_frame = len(frames_pulo) - 1

            TELA.blit(frames_pulo[pulo_frame], (x_jogador, y_jogador - 120))

            # Aterrissagem
            if y_jogador >= 580:
                y_jogador = 580
                velocidade_y = 0
                em_pulo = False

        else:
            # Corrida normal
            if tempo_corrida >= intervalo_corrida:
                frame_corrida = (frame_corrida + 1) % len(personagem_correndo)
                tempo_corrida = 0
            TELA.blit(personagem_correndo[frame_corrida], (x_jogador, y_jogador - 120))

        # Desenhar partículas de força
        for p in particulas_forca[:]:
            pygame.draw.circle(TELA, p["cor"], (int(p["x"]), int(p["y"])), 5)
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vy"] += 0.3
            p["vida"] -= 1
            if p["vida"] <= 0:
                particulas_forca.remove(p)

        desenhar_barra_forca(forca_lida)

        # Pontuação em tempo real
        pontuacao_texto = fonte_padrao.render(f"Pontos: {pontuacao}", True, COR_TEXTO)
        TELA.blit(pontuacao_texto, (LARGURA - 200, 50))

        # === COLISÃO ===
        jogador_rect = pygame.Rect(x_jogador + 20, y_jogador - 100, 80, 100)  # Hitbox ajustada

        for obstaculo in obstaculos:
            rect_real = obstaculo["rect"]
            if obstaculo["img"] == img_pedra:
                col_rect = pygame.Rect(rect_real.x + 20, rect_real.y + 20, rect_real.width - 40, rect_real.height - 40)
            else:
                col_rect = rect_real

            if jogador_rect.colliderect(col_rect):
                tempo_sessao_final = time.time() - tempo_inicio
                ESTADO = "resultados"  # Vai para resultados em vez de menu

    pygame.display.flip()
    clock.tick(FPS)