# 🎵 Gerenciador de Capas e Metadados para MP3

> 🇺🇸 [Read this in English](README.en.md)
> 🌍 Disponível em **5 idiomas**: Português, English, Español, 日本語, 한국어

Ferramenta genérica para gerenciar **capas** e **metadados** de arquivos MP3, com **perfis configuráveis** para diferentes dispositivos (feature phones, players antigos, celulares modernos, etc).

Desenvolvido pensando em aparelhos que exigem formatos específicos de tag ID3 — como o **Flip Vita 4G** (chip Unisoc UMS9117, Mocor OS) — mas funciona para qualquer MP3.

---

## ✨ Funcionalidades

### 📁 Aba Início
- Lista de MP3 com **miniatura da capa**, artista, álbum, ano e subpasta
- Filtros: "só sem capa", "só sem álbum", "só incompletas", etc
- Busca em tempo real por título, artista, álbum, ano ou gênero
- Ordenação clicando no cabeçalho das colunas
- **Duplo-clique na miniatura** = congelar/descongelar capa (🔒)
- **Duplo-clique na linha** = abrir editor de metadados
- **Duplo-clique na coluna Álbum** = selecionar todas as faixas do mesmo álbum
- Player de música com botões estilo YouTube Music
- Barra de progresso clicável/arrastável
- Botão "Normalizar TODAS" (aplica o perfil a toda a pasta)

### 🎼 Aba Playlist
- Lista playlists (subpastas) em ordem customizável
- Botões desenhados para mover músicas: ⬆⬆ Topo / ⬆ Subir / ⬇ Descer / ⬇⬇ Fim
- Botão **"Aplicar e renomear"** — renomeia os arquivos com prefixo numérico (`01-musica.mp3`, `02-musica.mp3`, ...) para manter a ordem em qualquer aparelho
- Player completo com capa, título e artista

### 🎨 Editor de Metadados
- Busca paralela em **MusicBrainz**, **iTunes** e **Deezer**
- Modo **Título da música** (singles) ou **Álbum completo**
- **Mapeamento de faixas** estilo MP3tag com auto-associação por similaridade
- Edição inline (duplo-clique em Nº, Título ou Arquivo)
- Menu de contexto: associar, remover, auto-numerar, tirar dos nomes...
- Checkboxes ✓ para campos comuns (desmarcado preserva o original)
- Opção **"NÃO alterar a capa"** (mantém a original)
- Download automático de capas (Cover Art Archive, iTunes, Deezer)
- **Ctrl+Z / Ctrl+Y** para desfazer/refazer ações

### ⚙️ Perfis de destino
- Perfis salvos em `perfis.json`
- 2 perfis padrão:
  - **Flip Vita 4G**: ID3v2.3 UTF-16, sem TDRC, capa 250x250, grava ID3v1 também
  - **Universal**: máxima compatibilidade (Android, Windows, TV, aparelho de som, iPod antigo, etc)
- Criação/edição/remoção de perfis com modo avançado
- Ajuste de versão de tag, encoding, tamanho/qualidade da capa, frames mantidos e muito mais

### 🌓 Tema e idiomas
- Tema claro e escuro, com detecção automática do Windows
- Botões redondos desenhados em Canvas (sem emoji — funciona igual em qualquer SO)
- Interface em **5 idiomas**: Português, English, Español, 日本語, 한국어
- Troca de idioma em tempo real (na janela de Configurações)

### 🎓 Onboarding na primeira execução
- Tela de boas-vindas com escolha de idioma
- Escolha de tema (automático, claro ou escuro)
- **Tour interativo** destacando cada parte do programa

### 🔒 Capas congeladas
- Marque músicas para **nunca** terem a capa alterada
- Salvo em `covers_ignore.json`
- Aplicado pelo editor e pelo atalho de trocar capa
- **Não** aplicado pelo "Normalizar" (por decisão de projeto)

---

## 🚀 Instalação

### Opção 1 — Instalador (recomendado para usuários finais)

Baixe o `Instalador_GerenciadorCapas_v1.0.exe` na página de [Releases](../../releases), dê duplo-clique e siga o assistente. Não precisa de admin. Instala em: `C:\Users\<seu_usuario>\AppData\Local\Programs\GerenciadorCapas\`

### Opção 2 — Rodar direto do código (Windows, Linux ou macOS)

Requisitos:
- **Python 3.12+** (testado no 3.14)

Comandos (rode no terminal):

    git clone https://github.com/Kdu5411/gerenciador-capas-mp3.git
    cd gerenciador-capas-mp3

    python -m venv venv
    venv\Scripts\activate      # Windows
    # source venv/bin/activate # Linux/macOS

    pip install -r requirements.txt

    python Capas_por_musica.py

---

## 📦 Dependências

| Biblioteca | Para quê |
|---|---|
| `mutagen` | Leitura/escrita de tags ID3 |
| `Pillow` | Manipulação de imagens (capas) |
| `pygame-ce` | Player de áudio |
| `musicbrainzngs` | Busca online (MusicBrainz) |
| `requests` | Busca online (iTunes, Deezer, CAA) |
| `tkinterdnd2` | Arrastar-e-soltar imagens (opcional) |

Todas em `requirements.txt`.

---

## 🔧 Gerar o `.exe` (para quem quer distribuir)

Já vem com um arquivo `Capas_por_musica.spec` pronto para o PyInstaller.

Comandos:

    pip install pyinstaller
    python -m PyInstaller --clean --noconfirm Capas_por_musica.spec

O resultado fica em `dist/GerenciadorCapas/`.

Para gerar o instalador, você precisa do [Inno Setup 6](https://jrsoftware.org/isdl.php) instalado. Depois:

    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" instalador.iss

O instalador final fica em `installer/`.

---

## 📂 Estrutura do projeto

    Capas Python/
    ├── Capas_por_musica.py       # código principal
    ├── Capas_por_musica.spec     # script do PyInstaller
    ├── Instalador.iss            # script do Inno Setup
    ├── i18n.py                   # motor de tradução
    ├── i18n/                     # arquivos de tradução
    │   ├── pt_BR.json
    │   ├── en.json
    │   ├── es.json
    │   ├── ja.json
    │   └── ko.json
    ├── icon.png                  # ícone do programa
    ├── icon.ico                  # ícone gerado automaticamente
    ├── requirements.txt          # dependências
    ├── README.md                 # este arquivo
    ├── README.en.md              # versão em inglês
    ├── LICENSE                   # licença MIT
    ├── AUTHORS                   # autores
    └── .gitignore                # arquivos ignorados pelo Git

Os arquivos `config.json`, `perfis.json` e `covers_ignore.json` são gerados automaticamente na primeira execução, na mesma pasta do programa.

---

## 💡 Dicas de uso

- **Normalizar** = reescrever as tags no formato do perfil escolhido, **mantendo capa e metadados atuais**. Útil para deixar todos os MP3 no mesmo padrão técnico.
- **Congelar capa** = marcar uma música para que a capa dela **nunca** seja substituída (útil quando você tem a capa perfeita e não quer perder).
- **Renomear playlists com prefixo** = adiciona `01-`, `02-`, etc. nas pastas para que a ordem fique gravada no próprio sistema de arquivos. Essencial para aparelhos que ordenam por nome.

---

## 🤝 Contribuindo

Sugestões e melhorias são bem-vindas! Abra uma [issue](../../issues) ou mande um pull request.

Especialmente bem-vindas: **novas traduções** (é só adicionar um arquivo `.json` na pasta `i18n/` e registrar em `i18n.py`).

---

## 📄 Licença

Este projeto está sob a licença **MIT** — veja [LICENSE](LICENSE) para mais detalhes.

## 👤 Autor

**Carlos Eduardo Loffreda Custodio** ([@Kdu5411](https://github.com/Kdu5411))

## 🙏 Agradecimentos

- Ícone por [Flaticon](https://www.flaticon.com)
- [MusicBrainz](https://musicbrainz.org/) por manter um banco de dados musical aberto e gratuito
- [Cover Art Archive](https://coverartarchive.org/) pelas capas
- [iTunes Search API](https://performance-partners.apple.com/search-api) e [Deezer API](https://developers.deezer.com/api) pelas buscas
- Comunidade Python, `mutagen`, `Pillow`, `pygame-ce` e `tkinterdnd2`