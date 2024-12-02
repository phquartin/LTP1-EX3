import pygame
import os
import random
import pyodbc
import math
import pygame.gfxdraw

# Iniciando DB
import sqlite3

def conectar_ou_criar_banco():
    # Conecta ao banco de dados ou cria se não existir
    conexao = sqlite3.connect("flappybird.db")
    cursor = conexao.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Jogador (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        NomeJogador TEXT NOT NULL,
        Recorde INTEGER NOT NULL,
        data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    print("Banco de dados conectado e tabela verificada/criada com sucesso.")
    return conexao, cursor

conexao, cursor = conectar_ou_criar_banco()

# Cores
PRETO = (0, 0, 0)
BRANCO = (255, 255, 255)
VERMELHO = (255, 0, 0)
AZUL_ESCURO = (0, 0, 50)

# Tamanho da TELA
TELA_LARGURA = 1000
TELA_ALTURA = 800

# Imagens
IMAGEM_CANO = pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'pipe.png')))
IMAGEM_CHAO = pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'base.png')))
IMAGEM_BACKGROUND = pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'bg.png')))
IMAGENS_PASSARO = [
    pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'bird1.png'))),
    pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'bird2.png'))),
    pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'bird3.png')))
]

# Configuração da fonte e do som
pygame.font.init()
pygame.display.set_caption('Flappy Bird')
pygame.mixer.init()
pygame.mixer.music.set_volume(0.1)
SOM_GAME_OVER = pygame.mixer.Sound(os.path.join('sons', 'fail.mp3'))


class Passaro:
    IMGS = IMAGENS_PASSARO

    # Animações de rotação
    ROTACAO_MAXIMA = 25
    VELOCIDADE_ROTACAO = 20
    TEMPO_ANIMACAO = 5

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.angulo = 0
        self.velocidade = 0
        self.altura = self.y
        self.tempo = 0
        self.contagem_imagem = 0
        self.imagem = self.IMGS[0]

    def pular(self):
        self.velocidade = -10.5
        self.tempo = 0
        self.altura = self.y

    def mover(self):
        # calcular o deslocamento
        self.tempo += 1
        deslocamento = 1.5 * (self.tempo ** 2) + self.velocidade * self.tempo  # FORMULA

        # restringir o deslocamento
        if deslocamento > 16:
            deslocamento = 16
        elif deslocamento < 0:
            deslocamento -= 2  # testar sem

        self.y += deslocamento

        # angulo do passaro
        if deslocamento < 0 or self.y < (self.altura + 50):  # testar sem
            if self.angulo < self.ROTACAO_MAXIMA:
                self.angulo = self.ROTACAO_MAXIMA
        else:
            if self.angulo > -90:
                self.angulo -= self.VELOCIDADE_ROTACAO

    def desenhar(self, tela):
        # definir imagem do passaro que vai ser usada
        self.contagem_imagem += 1

        if self.contagem_imagem < self.TEMPO_ANIMACAO:
            self.imagem = self.IMGS[0]
        elif self.contagem_imagem < self.TEMPO_ANIMACAO * 2:
            self.imagem = self.IMGS[1]
        elif self.contagem_imagem < self.TEMPO_ANIMACAO * 3:
            self.imagem = self.IMGS[2]
        elif self.contagem_imagem < self.TEMPO_ANIMACAO * 4:
            self.imagem = self.IMGS[1]
        elif self.contagem_imagem > self.TEMPO_ANIMACAO * 4:
            self.imagem = self.IMGS[0]
            self.contagem_imagem = 0

        # se o passaro estiver caindo, não vai ter batida de asa
        if self.angulo <= -80:
            self.imagem = self.IMGS[1]
            self.contagem_imagem = self.TEMPO_ANIMACAO * 2

        # desenhar imagem
        imagem_rotacionada = pygame.transform.rotate(self.imagem, self.angulo)
        pos_centro_imagem = imagem_rotacionada.get_rect(topleft=(self.x, self.y)).center
        retangulo = imagem_rotacionada.get_rect(center=pos_centro_imagem)
        tela.blit(imagem_rotacionada, retangulo.topleft)

    def get_mask(self):
        return pygame.mask.from_surface(self.imagem)


class Cano:
    DISTANCIA = 200

    def __init__(self, x):
        self.x = x
        self.altura = 0
        self.pos_topo = 0
        self.pos_base = 0
        self.velocidade = 5
        self.CANO_TOPO = pygame.transform.flip(IMAGEM_CANO, False, True)
        self.CANO_BASE = IMAGEM_CANO
        self.passou = False
        self.definir_altura()

    def definir_altura(self):
        self.altura = random.randrange(50, 450)
        self.pos_topo = self.altura - self.CANO_TOPO.get_height()
        self.pos_base = self.altura + self.DISTANCIA

    def mover(self):
        self.x -= self.velocidade

    def desenhar(self, tela):
        tela.blit(self.CANO_BASE, (self.x, self.pos_base))
        tela.blit(self.CANO_TOPO, (self.x, self.pos_topo))

    def colidir(self, passaro):
        passaro_mask = passaro.get_mask()
        topo_mask = pygame.mask.from_surface(self.CANO_TOPO)
        base_mask = pygame.mask.from_surface(self.CANO_BASE)

        distancia_topo = (self.x - round(passaro.x), self.pos_topo - round(passaro.y))
        distancia_base = (self.x - round(passaro.x), self.pos_base - round(passaro.y))

        base_ponto = passaro_mask.overlap(base_mask, distancia_base)
        topo_ponto = passaro_mask.overlap(topo_mask, distancia_topo)

        if base_ponto or topo_ponto:
            return True
        return False


class Chao:
    LARGURA = IMAGEM_CHAO.get_width()
    IMAGEM = IMAGEM_CHAO

    def __init__(self, y):
        self.y = y
        self.velocidade = 5
        self.x1 = 0
        self.x2 = self.LARGURA
        self.x3 = self.LARGURA + self.LARGURA

    def mover(self):
        self.x1 -= self.velocidade
        self.x2 -= self.velocidade
        self.x3 -= self.velocidade

        if self.x1 + self.LARGURA < 0:
            self.x1 = self.x3 + self.LARGURA
        if self.x2 + self.LARGURA < 0:
            self.x2 = self.x1 + self.LARGURA
        if self.x3 + self.LARGURA < 0:
            self.x3 = self.x2 + self.LARGURA

    def desenhar(self, tela):
        tela.blit(self.IMAGEM, (self.x1, self.y))
        tela.blit(self.IMAGEM, (self.x2, self.y))
        tela.blit(self.IMAGEM, (self.x3, self.y))


def desenhar_tela(tela, passaros, canos, chao, pontos, game_over, melhor_pontuacao, tela_inicio):
    tela.blit(IMAGEM_BACKGROUND, (0, 0))
    tela.blit(IMAGEM_BACKGROUND, (500, 0))
    for passaro in passaros:
        passaro.desenhar(tela)
    for cano in canos:
        cano.desenhar(tela)

    # Fonte
    fonte_pontos = pygame.font.SysFont('Arial', 80, bold=True)
    sombra_pontos = fonte_pontos.render(f'{pontos}', True, PRETO)
    texto_pontos = fonte_pontos.render(f'{pontos}', 1, BRANCO)
    chao.desenhar(tela)

    # Caso seja recorde, vai mostrar de um jeito diferente
    recorde = False
    if game_over:
        if pontos == melhor_pontuacao:
            recorde = True
        desenha_tela_game_over(pontos, tela, melhor_pontuacao, recorde)

    elif tela_inicio:
        desenhar_tela_inicio(tela)
    else:
        tela.blit(sombra_pontos, (TELA_LARGURA / 2 + 4, TELA_ALTURA / 2 + 4))
        tela.blit(texto_pontos, (TELA_LARGURA / 2, TELA_ALTURA / 2))

    pygame.display.update()


# Visual
def desenha_tela_game_over(score, tela, best, recorde=False):
    # Configurações da fonte
    fonte_titulo = pygame.font.SysFont("Arial", 70, bold=True)
    fonte_texto = pygame.font.SysFont("Arial", 30, bold=True)

    # Fundo semi-transparente
    overlay = pygame.Surface((TELA_LARGURA, TELA_ALTURA), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))  # Fundo escuro com transparência
    tela.blit(overlay, (0, 0))

    # Texto "Game Over" com efeito de sombra
    texto_game_over = fonte_titulo.render("GAME OVER", True, BRANCO)
    sombra_game_over = fonte_titulo.render("GAME OVER", True, PRETO)
    tela.blit(sombra_game_over, (TELA_LARGURA // 2 - sombra_game_over.get_width() // 2 + 3, TELA_ALTURA // 2 - 200 + 3))
    tela.blit(texto_game_over, (TELA_LARGURA // 2 - texto_game_over.get_width() // 2, TELA_ALTURA // 2 - 200))

    # Exibir pontuação final
    texto_pontuacao = fonte_texto.render(f"Pontuação: {score}", True, BRANCO)
    tela.blit(texto_pontuacao, (TELA_LARGURA // 2 - texto_pontuacao.get_width() // 2, TELA_ALTURA // 2 - 100))

    # Exibir Pontuação Recorde
    txt_recorde = f"Recorde: {best}"
    cor_recorde = VERMELHO
    if recorde:
        txt_recorde = f"Novo Recorde: {best}"
        cor_recorde = (200, 200, 0)
    texto_recorde = fonte_texto.render(txt_recorde, True, cor_recorde)
    tela.blit(texto_recorde, (TELA_LARGURA // 2 - texto_recorde.get_width() // 2, TELA_ALTURA // 2 - 50))
    # Botões de "Reiniciar" e "Menu Principal"
    texto_reiniciar = fonte_texto.render("Pressione R para Reiniciar", True, BRANCO)
    texto_menu = fonte_texto.render("Pressione T para o Ranking", True, BRANCO)
    tela.blit(texto_reiniciar, (TELA_LARGURA // 2 - texto_reiniciar.get_width() // 2, TELA_ALTURA // 2 + 50))
    tela.blit(texto_menu, (TELA_LARGURA // 2 - texto_menu.get_width() // 2, TELA_ALTURA // 2 + 100))

    pygame.display.flip()


def desenhar_tela_inicio(tela):
    # Superfície semi-transparente para o fundo da tela de início
    fundo_transparente = pygame.Surface((TELA_LARGURA, TELA_ALTURA), pygame.SRCALPHA)
    fundo_transparente.fill((0, 0, 0, 128))  # Fundo preto com 50% de transparência (128/255)
    tela.blit(fundo_transparente, (0, 0))  # Desenha a superfície na tela principal

    # Configurações de fontes e textos
    fonte_titulo = pygame.font.SysFont('Arial', 80, bold=True)
    fonte_texto = pygame.font.SysFont('Arial', 40)

    # Texto do título
    texto_titulo = fonte_titulo.render('Flappy Bird', True, (255, 255, 0))  # Cor amarela vibrante
    pos_titulo = ((TELA_LARGURA - texto_titulo.get_width()) // 2, TELA_ALTURA // 2 - 200)

    # Texto de instrução
    texto_instrucoes = fonte_texto.render('Pressione "ESPAÇO" para jogar', True, (255, 255, 255))
    pos_instrucoes = ((TELA_LARGURA - texto_instrucoes.get_width()) // 2, TELA_ALTURA // 2)

    # Animação de entrada: movimentos verticais dos textos
    deslocamento = 20  # Amplitude do movimento para cima e para baixo
    pos_titulo_animada = (pos_titulo[0], pos_titulo[1] + deslocamento * math.sin(pygame.time.get_ticks() / 300))

    # Desenha os textos na tela
    tela.blit(texto_titulo, pos_titulo_animada)
    tela.blit(texto_instrucoes, pos_instrucoes)

    pygame.display.update()


def desenhar_gradiente(tela, cor1, cor2):
    for y in range(TELA_ALTURA):
        cor_misturada = (
            cor1[0] + (cor2[0] - cor1[0]) * y // TELA_ALTURA,
            cor1[1] + (cor2[1] - cor1[1]) * y // TELA_ALTURA,
            cor1[2] + (cor2[2] - cor1[2]) * y // TELA_ALTURA
        )
        pygame.draw.line(tela, cor_misturada, (0, y), (TELA_LARGURA, y))


# Comandos SQL
def salvar_recorde(nome, pontos):
    cursor.execute("INSERT INTO Jogador (NomeJogador, Recorde) VALUES (?, ?)", (nome, pontos))
    conexao.commit()


# Exibir ranking com gradiente e destaque
def mostrar_ranking(tela):
    # Comando de busca SQL
    cursor.execute("SELECT NomeJogador, Recorde FROM Jogador ORDER BY Recorde DESC LIMIT 5")
    ranking = cursor.fetchall()

    # Fontes
    fonte_texto = pygame.font.SysFont("Arial", 30, bold=True)
    fonte_titulo = pygame.font.SysFont('Monospace', 50)
    fonte_nomes = pygame.font.SysFont('Sans-Serif', 40)

    # Visual
    desenhar_gradiente(tela, (30, 30, 60), (10, 10, 30))
    y_offset = 90  # Posição vertical inicial do ranking
    texto_ranking = fonte_titulo.render("RANKING (TOP 5)", 1, (255, 255, 255))
    tela.blit(texto_ranking, ((TELA_LARGURA - texto_ranking.get_width()) // 2, y_offset))
    y_offset += 150  # Distância Titulo -> Pontos

    # Mostrar Pontos com Loop
    for idx, (nome, pontos) in enumerate(ranking):
        texto_ranking = fonte_nomes.render(f"{idx + 1}. {nome}: {pontos} pontos", 1, (255, 255, 255))
        tela.blit(texto_ranking, ((TELA_LARGURA - texto_ranking.get_width()) // 2, y_offset))
        y_offset += 90  # Espaçamento entre linhas

    # Indicação de Volta
    texto_menu = fonte_texto.render("Pressione T para voltar", True, (100, 100, 100))
    tela.blit(texto_menu, ((TELA_LARGURA - texto_menu.get_width()) // 2, y_offset + 10))
    pygame.display.update()


# Captura de nome com confirmação
def capturar_nome(tela):
    nome = ""
    fonte_input = pygame.font.SysFont("Arial", 50, bold=True)
    fonte_pergunta = pygame.font.SysFont("Arial", 30)

    rodando = True
    while rodando:
        # Fundo semi-transparente para o input
        fundo_transparente = pygame.Surface((TELA_LARGURA, TELA_ALTURA), pygame.SRCALPHA)
        fundo_transparente.fill((0, 0, 0, 128))  # Fundo escuro com 50% de transparência
        tela.blit(fundo_transparente, (0, 0))

        # Texto da pergunta
        texto_pergunta = fonte_pergunta.render("Digite seu nome e pressione ENTER:", True, BRANCO)
        tela.blit(texto_pergunta, ((TELA_LARGURA - texto_pergunta.get_width()) // 2, TELA_ALTURA // 2 - 100))

        # Texto do nome sendo digitado
        texto_nome = fonte_input.render(nome, True, BRANCO)
        tela.blit(texto_nome, ((TELA_LARGURA - texto_nome.get_width()) // 2, TELA_ALTURA // 2))

        pygame.display.update()

        # Captura de eventos
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False
                pygame.quit()
                quit()
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_RETURN:
                    rodando = False
                elif evento.key == pygame.K_BACKSPACE:
                    nome = nome[:-1]
                else:
                    # Limita o nome a 10 caracteres para o ranking
                    if len(nome) < 10:
                        nome += evento.unicode

    return nome


def main():
    # Definindo variáveis de estado do jogo
    passaros = [Passaro(230, 350)]
    chao = Chao(730)
    canos = [Cano(1000), Cano(1500), Cano(2000)]
    tela = pygame.display.set_mode((TELA_LARGURA, TELA_ALTURA))
    nome = capturar_nome(tela)
    pontos = 0
    melhor_pontuacao = 0
    relogio = pygame.time.Clock()
    game_over = False
    tela_inicio = True
    mostrar_ranking_ativo = False

    rodando = True
    while rodando:
        relogio.tick(30)

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                cursor.close()
                conexao.close()
                rodando = False
                pygame.quit()
                quit()
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_SPACE and not game_over:
                    for passaro in passaros:
                        passaro.pular()
                if game_over:
                    if evento.key == pygame.K_r:  # Pressione 'R' para reiniciar
                        # Resetando as variáveis do jogo
                        passaros = [Passaro(230, 350)]
                        chao = Chao(730)
                        canos = [Cano(1000), Cano(1500), Cano(2000)]
                        pontos = 0
                        game_over = False  # Sai do estado de Game Over
                    if evento.key == pygame.K_t:
                        mostrar_ranking_ativo = not mostrar_ranking_ativo  # Alterna o estado do ranking

                if tela_inicio:
                    if evento.key == pygame.K_SPACE:  # INCIAR
                        passaros = [Passaro(230, 350)]
                        chao = Chao(730)
                        canos = [Cano(1000), Cano(1500), Cano(2000)]
                        pontos = 0
                        tela_inicio = False
                    if evento.key == pygame.K_t:
                        mostrar_ranking_ativo = not mostrar_ranking_ativo  # Alterna o estado do ranking

        if mostrar_ranking_ativo:
            mostrar_ranking(tela)
            continue  # Evita o movimento do jogo enquanto o ranking é exibido

        # Apenas movimenta os objetos e verifica colisões se não estiver em Game Over
        if not game_over and not tela_inicio:
            for passaro in passaros:
                passaro.mover()
            chao.mover()

            adicionar_cano = False
            remover_canos = []
            for cano in canos:
                for i, passaro in enumerate(passaros):
                    if cano.colidir(passaro):
                        SOM_GAME_OVER.play()
                        game_over = True  # Ativa o estado de Game Over
                        break
                    if not cano.passou and passaro.x > cano.x:
                        cano.passou = True
                        adicionar_cano = True
                cano.mover()
                if cano.x + cano.CANO_TOPO.get_width() < 0:
                    remover_canos.append(cano)

            if adicionar_cano:
                pontos += 1
                canos.append(Cano(1500))
            for cano in remover_canos:
                canos.remove(cano)

            for i, passaro in enumerate(passaros):
                if (passaro.y + passaro.imagem.get_height()) > chao.y or passaro.y < 0:
                    if not game_over:  # Garantir que o som de game over toca apenas uma vez
                        SOM_GAME_OVER.play()
                    game_over = True  # Ativa o estado de Game Over
                    break

        if pontos > melhor_pontuacao and game_over:
            melhor_pontuacao = pontos
            salvar_recorde(nome, pontos)

        # Desenha a tela
        desenhar_tela(tela, passaros, canos, chao, pontos, game_over, melhor_pontuacao, tela_inicio)


if __name__ == '__main__':
    main()
