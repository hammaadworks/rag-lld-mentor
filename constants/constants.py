PATTERN_YYYY_MM_DD = '%Y-%m-%d'
ASIA_KOLKATA = 'Asia/Kolkata'

NON_BREAKING_ELEMENTS = ['a', 'abbr', 'acronym', 'audio', 'b', 'bdi', 'bdo', 'big', 'button',
                         'canvas', 'cite', 'code', 'data', 'datalist', 'del', 'dfn', 'em', 'embed', 'i', 'iframe',
                         'img', 'input', 'ins', 'kbd', 'label', 'map', 'mark', 'meter', 'noscript', 'object', 'output',
                         'picture', 'progress', 'q', 'ruby', 's', 'samp', 'script', 'select', 'slot', 'small', 'span',
                         'strong', 'sub', 'sup', 'svg', 'template', 'textarea', 'time', 'u', 'tt', 'var', 'video',
                         'wbr']
SENTENCE_LENGTH = 30
MAX_BLANK_COUNT = 3
RENDER_TIMEOUT = 300.0
DEL_TAGS = [('section', 'site-slide-menu'), ('section', 'product__login-notice-bar'),
            ('mark', 'site-notification-v4rd'), ('header', 'site-header-v4rd'), ('div', 'xm-navbar')]
SOUP_HTML_PARSER = "html.parser"
CHUNK_SIZE = 3000
CHUNK_OVERLAP = 50
FAISS_STORE = "./vectorstore/faiss_store"
EMBEDDING_MODEL_MINI_LM = 'sentence-transformers/all-MiniLM-L6-v2'
EMBEDDING_MODEL_BGE_LARGE = 'BAAI/bge-large-en-v1.5'
EMBEDDING_MODEL = 'BAAI/bge-small-en-v1.5'
MAX_HISTORY_LENGTH = 5

MAIN_PROMPT_TEMPLATE = """The following is a friendly conversation between a human and an AI. 
    The AI is talkative and provides lots of specific details from its context.
    If the AI does not know the answer to a question, it truthfully says it does not know.
    Context: {context}
    Question: {question}
    Instruction: 
    1. Based on the above documents, provide a detailed answer for the above question. 
    2. Answer "Sorry, I don't know the answer" if not present in the document.
    Solution: """

STANDALONE_PROMPT_TEMPLATE = """Given the following conversation and a follow up question, 
    rephrase the follow up question to be a standalone question.
    Chat History: {chat_history}
    Follow Up Input: {question}
    Standalone question: """

GPT_3_5_TURBO = 'gpt-3.5-turbo'
GPT_4 = 'gpt-4o'
USER_ICON = "./images/user_icon.png"
AI_ICON = "./images/bot_icon.png"
APP_TITLE = "LLD-GPT"

CREATE_LOGIN_TABLE_SQL = ('''CREATE TABLE IF NOT EXISTS login_details (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                email TEXT UNIQUE,
                                name TEXT,
                                password TEXT
                                );''')

CREATE_CHAT_TABLE_SQL = ('''CREATE TABLE IF NOT EXISTS chat_history (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                email TEXT,
                                question TEXT,
                                answer TEXT,
                                date TEXT
                                );''')

DEFAULT_LOGIN_TABLE_SQL = ('''INSERT OR IGNORE INTO login_details (email, name, password) VALUES
                                ('hammaadworks@gmail.com', 'Mohammed Hammaad Abdul Mateen', 'P@ss_123'),
                                ('myfriendhammad@gmail.com', 'Mohammed Hammaad Abdul Mateen', 'P@ss_123'),
                                ('test_user@hammaad.com', 'Test User', 'P@ss_123');
                            ''')

RESET_CODE_LENGTH = 5
PASSWORD_LENGTH = 8
