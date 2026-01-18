import os
import re
import sys
import time
import yaml
import ctypes
import random
import string
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from pystyle import *
from colorama import Fore, Style, init
from threading import Semaphore, Lock
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
init()

try: os.system('cls')
except: pass

if not os.path.exists('proxy/output'):
    os.makedirs('proxy/output')
if not os.path.exists('proxy/input'):
    os.makedirs('proxy/input')

def getTimeStampForReq() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

def Sprint(tag, content, color):
    print(f"{Style.BRIGHT}{Fore.WHITE}[{Fore.BLUE}TOOL: {Fore.BLACK}{getTimeStampForReq()}{Fore.WHITE}] [{color}{tag}{Fore.WHITE}] {Fore.BLUE}- {Fore.WHITE}{content}{Style.RESET_ALL}")

# Charger la configuration
config_path = 'proxy/config.yaml'
if not os.path.exists(config_path):
    Sprint('!', 'Fichier config.yaml non trouvé, création avec valeurs par défaut...', Fore.YELLOW)
    default_config = {
        'threads': 10,
        'request_timeout': 10,
        'request_delay': 0.5,
        'test_url': 'http://httpbin.org/ip',
        'update_title': True,
        'print_invalid': False,
        'max_retries': 2
    }
    os.makedirs('proxy', exist_ok=True)
    with open(config_path, 'w') as f:
        yaml.dump(default_config, f, default_flow_style=False)

with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

try:
    threads_config = config.get("threads", 10)
    request_timeout = config.get("request_timeout", 10)
    request_delay = config.get("request_delay", 0.5)
    test_url = config.get("test_url", "http://httpbin.org/ip")
    update_ttl = config.get("update_title", True)
    p_inv = config.get("print_invalid", False)
    max_retries = config.get("max_retries", 2)
except:
    print("Vérifiez votre config.yaml !")
    time.sleep(10)
    sys.exit(0)

rate_limit_semaphore = None
last_request_time = 0
request_lock = Lock()

def update_title(title):
    if update_ttl:
        try:
            ctypes.windll.kernel32.SetConsoleTitleW(title)
        except:
            pass

def rate_limit_request():
    global last_request_time
    with request_lock:
        current_time = time.time()
        time_since_last = current_time - last_request_time
        if time_since_last < request_delay:
            time.sleep(request_delay - time_since_last)
        last_request_time = time.time()
        time.sleep(random.uniform(0.05, 0.15))

# Statistiques globales
valid_count = 0
invalid_count = 0
timeout_count = 0

def show_banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    ascii_text = '''
             ██╗  ██╗██████╗ ██╗██╗  ██╗    ██████╗ ██████╗  ██████╗ ██╗  ██╗██╗   ██╗
             ██║ ██╔╝██╔══██╗██║╚██╗██╔╝    ██╔══██╗██╔══██╗██╔═══██╗╚██╗██╔╝╚██╗ ██╔╝
             █████╔╝ ██████╔╝██║ ╚███╔╝     ██████╔╝██████╔╝██║   ██║ ╚███╔╝  ╚████╔╝ 
             ██╔═██╗ ██╔══██╗██║ ██╔██╗     ██╔═══╝ ██╔══██╗██║   ██║ ██╔██╗   ╚██╔╝  
             ██║  ██╗██║  ██║██║██╔╝ ██╗    ██║     ██║  ██║╚██████╔╝██╔╝ ██╗   ██║   
             ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═╝    ╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝   
    '''
    print(Colorate.Horizontal(Colors.blue_to_purple, Center.XCenter(ascii_text)))
    print('')

def generate_random_ip():
    """Génère une adresse IP aléatoire réaliste"""
    # Éviter les plages privées et invalides
    first = random.choice([random.randint(1, 126), random.randint(128, 191), random.randint(192, 223)])
    return f"{first}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"

def generate_random_port():
    """Génère un port aléatoire réaliste pour les proxies"""
    # Ports communs pour proxies: 80, 8080, 3128, 1080, etc.
    common_ports = [80, 8080, 3128, 8888, 1080, 9050, 8000, 3129, 8081, 9999]
    if random.random() < 0.5:
        return random.choice(common_ports)
    return random.randint(1024, 65535)

def generate_proxy(proxy_type, with_auth=False):
    """Génère un proxy aléatoire au format IP:PORT ou user:pass@IP:PORT"""
    ip = generate_random_ip()
    port = generate_random_port()
    
    if with_auth:
        username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=random.randint(6, 12)))
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(8, 16)))
        return f"{username}:{password}@{ip}:{port}"
    else:
        return f"{ip}:{port}"

def option_generate_and_check():
    """Option 1: Générer et vérifier des proxies"""
    global valid_count, invalid_count, timeout_count, rate_limit_semaphore
    
    show_banner()
    print(f'{Fore.WHITE}[{Fore.BLUE}1{Fore.WHITE}] {Fore.BLUE}- {Fore.WHITE}Générer et Vérifier des Proxies')
    print('')
    
    # Demander le nombre
    num_str = input(f'{Style.BRIGHT}{Fore.WHITE}[{Fore.BLUE}?{Fore.WHITE}] {Fore.MAGENTA}- {Fore.WHITE}Combien de proxies générer? {Fore.RED}>>> {Fore.WHITE}')
    while not num_str.isdigit() or int(num_str) <= 0:
        print(f"{Style.BRIGHT}{Fore.WHITE}[{Fore.YELLOW}!{Fore.WHITE}] {Fore.MAGENTA}- {Fore.WHITE}Entrée invalide.")
        num_str = input(f'{Style.BRIGHT}{Fore.WHITE}[{Fore.BLUE}?{Fore.WHITE}] {Fore.MAGENTA}- {Fore.WHITE}Entrez un nombre valide {Fore.RED}>>> {Fore.WHITE}')
    num = int(num_str)
    
    # Demander le type
    print('')
    print(f'{Fore.WHITE}[{Fore.BLUE}?{Fore.WHITE}] {Fore.BLUE}- {Fore.WHITE}Types de proxy disponibles:')
    print(f'{Fore.WHITE}[{Fore.BLUE}1{Fore.WHITE}] {Fore.MAGENTA}- {Fore.WHITE}HTTP')
    print(f'{Fore.WHITE}[{Fore.BLUE}2{Fore.WHITE}] {Fore.MAGENTA}- {Fore.WHITE}HTTPS')
    print(f'{Fore.WHITE}[{Fore.BLUE}3{Fore.WHITE}] {Fore.MAGENTA}- {Fore.WHITE}SOCKS4')
    print(f'{Fore.WHITE}[{Fore.BLUE}4{Fore.WHITE}] {Fore.MAGENTA}- {Fore.WHITE}SOCKS5')
    print(f'{Fore.WHITE}[{Fore.BLUE}5{Fore.WHITE}] {Fore.MAGENTA}- {Fore.WHITE}Tous les types (mélangés)')
    
    choice = input(f'{Style.BRIGHT}{Fore.WHITE}[{Fore.BLUE}?{Fore.WHITE}] {Fore.MAGENTA}- {Fore.WHITE}Sélectionnez le type {Fore.RED}>>> {Fore.WHITE}')
    while choice not in ['1', '2', '3', '4', '5']:
        print(f"{Style.BRIGHT}{Fore.WHITE}[{Fore.YELLOW}!{Fore.WHITE}] {Fore.MAGENTA}- {Fore.WHITE}Choix invalide.")
        choice = input(f'{Style.BRIGHT}{Fore.WHITE}[{Fore.BLUE}?{Fore.WHITE}] {Fore.MAGENTA}- {Fore.WHITE}Sélectionnez un choix valide {Fore.RED}>>> {Fore.WHITE}')
    
    types_map = {'1': 'HTTP', '2': 'HTTPS', '3': 'SOCKS4', '4': 'SOCKS5', '5': 'ALL'}
    proxy_type = types_map[choice]
    
    # Demander délai
    print('')
    delay_str = input(f'{Style.BRIGHT}{Fore.WHITE}[{Fore.BLUE}?{Fore.WHITE}] {Fore.MAGENTA}- {Fore.WHITE}Délai entre générations (secondes, 0 pour aucun)? {Fore.RED}>>> {Fore.WHITE}')
    try:
        delay = float(delay_str)
    except:
        delay = 0
    
    print('')
    Sprint('!', f'Génération de {num} proxies de type {proxy_type}...', Fore.CYAN)
    
    # Générer les proxies
    proxies = []
    for i in range(num):
        if proxy_type == 'ALL':
            current_type = random.choice(['HTTP', 'HTTPS', 'SOCKS4', 'SOCKS5'])
        else:
            current_type = proxy_type
        
        proxy = generate_proxy(current_type, False)  # Sans auth pour la vérification
        proxies.append(f"{current_type}://{proxy}")
        
        if (i + 1) % 10 == 0:
            Sprint('>', f'Généré {i + 1}/{num} proxies...', Fore.BLUE)
        
        if delay > 0:
            time.sleep(delay)
    
    # Demander le nombre de threads pour la vérification
    print('')
    Sprint('!', f'{len(proxies)} proxies générés. Début de la vérification...', Fore.CYAN)
    threads_str = input(f'{Style.BRIGHT}{Fore.WHITE}[{Fore.BLUE}?{Fore.WHITE}] {Fore.MAGENTA}- {Fore.WHITE}Nombre de threads (défaut: {threads_config})? {Fore.RED}>>> {Fore.WHITE}')
    if threads_str.isdigit() and int(threads_str) > 0:
        threads = int(threads_str)
    else:
        threads = threads_config
    
    print('')
    Sprint('!', f'Vérification avec {threads} threads...', Fore.CYAN)
    print('')
    
    # Réinitialiser les compteurs
    valid_count = 0
    invalid_count = 0
    timeout_count = 0
    
    # Créer le semaphore
    rate_limit_semaphore = Semaphore(threads)
    
    # Résultats
    results = {'VALID': [], 'INVALID': [], 'TIMEOUT': []}
    
    def process_proxy(proxy_line):
        try:
            checker = ProxyChecker(proxy_line)
            result = checker.check()
            results[result].append(proxy_line)
        except Exception as e:
            Sprint('-', f'Erreur critique sur proxy {proxy_line}: {e}', Fore.RED)
            results['INVALID'].append(proxy_line)
    
    # Vérifier en multi-thread
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = [executor.submit(process_proxy, proxy) for proxy in proxies]
        for future in as_completed(futures):
            future.result()
    
    elapsed = time.time() - start_time
    
    # Sauvegarder les résultats
    with open('proxy/output/valid_proxies.txt', 'w') as f:
        for proxy in results['VALID']:
            f.write(proxy + '\n')
    
    with open('proxy/output/invalid_proxies.txt', 'w') as f:
        for proxy in results['INVALID']:
            f.write(proxy + '\n')
    
    with open('proxy/output/timeout_proxies.txt', 'w') as f:
        for proxy in results['TIMEOUT']:
            f.write(proxy + '\n')
    
    # Afficher les résultats
    print('')
    Sprint('#', f'Vérification terminée en {elapsed:.2f}s', Fore.BLUE)
    print('')
    Sprint('#', f'Total traités: {Fore.BLUE}{len(proxies)}', Fore.BLUE)
    Sprint('#', f'Valides: {Fore.GREEN}{valid_count}', Fore.GREEN)
    Sprint('#', f'Invalides: {Fore.RED}{invalid_count}', Fore.RED)
    Sprint('#', f'Timeouts: {Fore.YELLOW}{timeout_count}', Fore.YELLOW)
    print('')
    Sprint('!', f'Résultats sauvegardés dans proxy/output/', Fore.CYAN)
    print('')
    input(f'{Style.BRIGHT}{Fore.WHITE}[{Fore.BLUE}?{Fore.WHITE}] {Fore.MAGENTA}- {Fore.WHITE}Appuyez sur {Fore.BLUE}Entrée {Fore.WHITE}pour continuer...')

class ProxyChecker:
    def __init__(self, proxy_line: str) -> None:
        self.original = proxy_line.strip()
        self.proxy_dict = None
        self.proxy_type = None
        self.valid = False
        
        # Parser le proxy
        self.parse_proxy()
        
    def parse_proxy(self):
        """Parse différents formats de proxy"""
        try:
            # Format: TYPE://IP:PORT ou TYPE://user:pass@IP:PORT
            if '://' in self.original:
                parts = self.original.split('://', 1)
                self.proxy_type = parts[0].upper()
                proxy_str = parts[1]
            else:
                # Format: IP:PORT (assume HTTP par défaut)
                self.proxy_type = 'HTTP'
                proxy_str = self.original
            
            # Construire le dict de proxy pour requests
            if self.proxy_type in ['SOCKS4', 'SOCKS5']:
                self.proxy_dict = {
                    'http': f'socks5://{proxy_str}' if self.proxy_type == 'SOCKS5' else f'socks4://{proxy_str}',
                    'https': f'socks5://{proxy_str}' if self.proxy_type == 'SOCKS5' else f'socks4://{proxy_str}'
                }
            else:
                self.proxy_dict = {
                    'http': f'http://{proxy_str}',
                    'https': f'https://{proxy_str}'
                }
        except Exception as e:
            Sprint('-', f'Erreur parsing proxy {self.original}: {e}', Fore.RED)
            self.proxy_dict = None
    
    def check(self, retry_count=0) -> str:
        """Vérifie le proxy. Retourne: 'VALID', 'INVALID', ou 'TIMEOUT'"""
        global valid_count, invalid_count, timeout_count
        
        if self.proxy_dict is None:
            invalid_count += 1
            update_title(f'KRIX PROXY - Valides: {valid_count}, Invalides: {invalid_count}, Timeouts: {timeout_count}')
            Sprint('-', f'Proxy invalide (format): {Fore.RED}{self.original}', Fore.RED)
            return 'INVALID'
        
        semaphore_acquired = False
        try:
            rate_limit_semaphore.acquire()
            semaphore_acquired = True
            rate_limit_request()
            
            response = requests.get(test_url, proxies=self.proxy_dict, timeout=request_timeout, verify=False)
            
            if response.status_code == 200:
                valid_count += 1
                update_title(f'KRIX PROXY - Valides: {valid_count}, Invalides: {invalid_count}, Timeouts: {timeout_count}')
                Sprint('+', f'Proxy valide: {Fore.GREEN}{self.original}', Fore.GREEN)
                return 'VALID'
            else:
                invalid_count += 1
                update_title(f'KRIX PROXY - Valides: {valid_count}, Invalides: {invalid_count}, Timeouts: {timeout_count}')
                Sprint('-', f'Proxy invalide (code {response.status_code}): {Fore.RED}{self.original}', Fore.RED)
                return 'INVALID'
                
        except requests.exceptions.Timeout:
            timeout_count += 1
            update_title(f'KRIX PROXY - Valides: {valid_count}, Invalides: {invalid_count}, Timeouts: {timeout_count}')
            Sprint('!', f'Proxy timeout: {Fore.YELLOW}{self.original}', Fore.YELLOW)
            return 'TIMEOUT'
            
        except requests.exceptions.ProxyError as e:
            invalid_count += 1
            update_title(f'KRIX PROXY - Valides: {valid_count}, Invalides: {invalid_count}, Timeouts: {timeout_count}')
            Sprint('-', f'Proxy erreur connexion: {Fore.RED}{self.original}', Fore.RED)
            return 'INVALID'
            
        except requests.exceptions.ConnectionError as e:
            if retry_count < max_retries:
                if semaphore_acquired:
                    rate_limit_semaphore.release()
                    semaphore_acquired = False
                time.sleep(1)
                return self.check(retry_count + 1)
            
            timeout_count += 1
            update_title(f'KRIX PROXY - Valides: {valid_count}, Invalides: {invalid_count}, Timeouts: {timeout_count}')
            Sprint('!', f'Proxy timeout (connexion): {Fore.YELLOW}{self.original}', Fore.YELLOW)
            return 'TIMEOUT'
            
        except Exception as e:
            if retry_count < max_retries:
                if semaphore_acquired:
                    rate_limit_semaphore.release()
                    semaphore_acquired = False
                time.sleep(1)
                return self.check(retry_count + 1)
            
            invalid_count += 1
            update_title(f'KRIX PROXY - Valides: {valid_count}, Invalides: {invalid_count}, Timeouts: {timeout_count}')
            Sprint('-', f'Proxy erreur: {Fore.RED}{self.original} - {str(e)[:50]}', Fore.RED)
            return 'INVALID'
        finally:
            if semaphore_acquired:
                rate_limit_semaphore.release()

def option_check_proxies():
    """Option 2: Vérifier les proxies depuis un fichier"""
    global valid_count, invalid_count, timeout_count, rate_limit_semaphore
    
    show_banner()
    print(f'{Fore.WHITE}[{Fore.BLUE}2{Fore.WHITE}] {Fore.BLUE}- {Fore.WHITE}Vérification de Proxies')
    print('')
    
    # Charger les proxies
    proxy_file = 'proxy/input/proxies.txt'
    if not os.path.exists(proxy_file):
        Sprint('-', f'Fichier {proxy_file} non trouvé!', Fore.RED)
        print('')
        input(f'{Style.BRIGHT}{Fore.WHITE}[{Fore.BLUE}?{Fore.WHITE}] {Fore.MAGENTA}- {Fore.WHITE}Appuyez sur {Fore.BLUE}Entrée {Fore.WHITE}pour continuer...')
        return
    
    with open(proxy_file, 'r', encoding='utf-8') as f:
        proxies = [line.strip() for line in f if line.strip()]
    
    if not proxies:
        Sprint('-', f'Aucun proxy trouvé dans {proxy_file}!', Fore.RED)
        print('')
        input(f'{Style.BRIGHT}{Fore.WHITE}[{Fore.BLUE}?{Fore.WHITE}] {Fore.MAGENTA}- {Fore.WHITE}Appuyez sur {Fore.BLUE}Entrée {Fore.WHITE}pour continuer...')
        return
    
    # Demander le nombre de threads
    threads_str = input(f'{Style.BRIGHT}{Fore.WHITE}[{Fore.BLUE}?{Fore.WHITE}] {Fore.MAGENTA}- {Fore.WHITE}Nombre de threads (défaut: {threads_config})? {Fore.RED}>>> {Fore.WHITE}')
    if threads_str.isdigit() and int(threads_str) > 0:
        threads = int(threads_str)
    else:
        threads = threads_config
    
    print('')
    Sprint('!', f'{len(proxies)} proxies chargés depuis {proxy_file}', Fore.CYAN)
    Sprint('!', f'Vérification avec {threads} threads...', Fore.CYAN)
    print('')
    
    # Réinitialiser les compteurs
    valid_count = 0
    invalid_count = 0
    timeout_count = 0
    
    # Créer le semaphore
    rate_limit_semaphore = Semaphore(threads)
    
    # Résultats
    results = {'VALID': [], 'INVALID': [], 'TIMEOUT': []}
    
    def process_proxy(proxy_line):
        try:
            checker = ProxyChecker(proxy_line)
            result = checker.check()
            results[result].append(proxy_line)
        except Exception as e:
            Sprint('-', f'Erreur critique sur proxy {proxy_line}: {e}', Fore.RED)
            results['INVALID'].append(proxy_line)
    
    # Vérifier en multi-thread
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = [executor.submit(process_proxy, proxy) for proxy in proxies]
        for future in as_completed(futures):
            future.result()
    
    elapsed = time.time() - start_time
    
    # Sauvegarder les résultats
    with open('proxy/output/valid_proxies.txt', 'w') as f:
        for proxy in results['VALID']:
            f.write(proxy + '\n')
    
    with open('proxy/output/invalid_proxies.txt', 'w') as f:
        for proxy in results['INVALID']:
            f.write(proxy + '\n')
    
    with open('proxy/output/timeout_proxies.txt', 'w') as f:
        for proxy in results['TIMEOUT']:
            f.write(proxy + '\n')
    
    # Afficher les résultats
    print('')
    Sprint('#', f'Vérification terminée en {elapsed:.2f}s', Fore.BLUE)
    print('')
    Sprint('#', f'Total traités: {Fore.BLUE}{len(proxies)}', Fore.BLUE)
    Sprint('#', f'Valides: {Fore.GREEN}{valid_count}', Fore.GREEN)
    Sprint('#', f'Invalides: {Fore.RED}{invalid_count}', Fore.RED)
    Sprint('#', f'Timeouts: {Fore.YELLOW}{timeout_count}', Fore.YELLOW)
    print('')
    Sprint('!', f'Résultats sauvegardés dans proxy/output/', Fore.CYAN)
    print('')
    input(f'{Style.BRIGHT}{Fore.WHITE}[{Fore.BLUE}?{Fore.WHITE}] {Fore.MAGENTA}- {Fore.WHITE}Appuyez sur {Fore.BLUE}Entrée {Fore.WHITE}pour continuer...')

def option_config():
    """Option 3: Modifier la configuration"""
    show_banner()
    print(f'{Fore.WHITE}[{Fore.BLUE}3{Fore.WHITE}] {Fore.BLUE}- {Fore.WHITE}Configuration')
    print('')
    
    print(f'{Fore.WHITE}[{Fore.BLUE}%{Fore.WHITE}] {Fore.BLUE}- {Fore.WHITE}Configuration actuelle:')
    print(f'{Fore.WHITE}[{Fore.BLUE}1{Fore.WHITE}] {Fore.MAGENTA}- {Fore.WHITE}Threads:         {Fore.BLUE}{threads_config}')
    print(f'{Fore.WHITE}[{Fore.BLUE}2{Fore.WHITE}] {Fore.MAGENTA}- {Fore.WHITE}Timeout:         {Fore.BLUE}{request_timeout}s')
    print(f'{Fore.WHITE}[{Fore.BLUE}3{Fore.WHITE}] {Fore.MAGENTA}- {Fore.WHITE}Délai requêtes:  {Fore.BLUE}{request_delay}s')
    print(f'{Fore.WHITE}[{Fore.BLUE}4{Fore.WHITE}] {Fore.MAGENTA}- {Fore.WHITE}URL de test:     {Fore.BLUE}{test_url}')
    print(f'{Fore.WHITE}[{Fore.BLUE}5{Fore.WHITE}] {Fore.MAGENTA}- {Fore.WHITE}Update title:    {Fore.BLUE}{update_ttl}')
    print(f'{Fore.WHITE}[{Fore.BLUE}6{Fore.WHITE}] {Fore.MAGENTA}- {Fore.WHITE}Print invalid:   {Fore.BLUE}{p_inv}')
    print(f'{Fore.WHITE}[{Fore.BLUE}7{Fore.WHITE}] {Fore.MAGENTA}- {Fore.WHITE}Max retries:     {Fore.BLUE}{max_retries}')
    print('')
    
    choice = input(f'{Style.BRIGHT}{Fore.WHITE}[{Fore.BLUE}?{Fore.WHITE}] {Fore.MAGENTA}- {Fore.WHITE}Paramètre à modifier (1-7, 0 pour annuler) {Fore.RED}>>> {Fore.WHITE}')
    
    if choice == '0':
        return
    
    new_config = config.copy()
    
    if choice == '1':
        val = input(f'{Style.BRIGHT}{Fore.WHITE}[{Fore.BLUE}?{Fore.WHITE}] {Fore.MAGENTA}- {Fore.WHITE}Nouveau nombre de threads {Fore.RED}>>> {Fore.WHITE}')
        if val.isdigit():
            new_config['threads'] = int(val)
    elif choice == '2':
        val = input(f'{Style.BRIGHT}{Fore.WHITE}[{Fore.BLUE}?{Fore.WHITE}] {Fore.MAGENTA}- {Fore.WHITE}Nouveau timeout (secondes) {Fore.RED}>>> {Fore.WHITE}')
        try:
            new_config['request_timeout'] = float(val)
        except:
            pass
    elif choice == '3':
        val = input(f'{Style.BRIGHT}{Fore.WHITE}[{Fore.BLUE}?{Fore.WHITE}] {Fore.MAGENTA}- {Fore.WHITE}Nouveau délai entre requêtes (secondes) {Fore.RED}>>> {Fore.WHITE}')
        try:
            new_config['request_delay'] = float(val)
        except:
            pass
    elif choice == '4':
        val = input(f'{Style.BRIGHT}{Fore.WHITE}[{Fore.BLUE}?{Fore.WHITE}] {Fore.MAGENTA}- {Fore.WHITE}Nouvelle URL de test {Fore.RED}>>> {Fore.WHITE}')
        if val.strip():
            new_config['test_url'] = val.strip()
    elif choice == '5':
        val = input(f'{Style.BRIGHT}{Fore.WHITE}[{Fore.BLUE}?{Fore.WHITE}] {Fore.MAGENTA}- {Fore.WHITE}Update title? (true/false) {Fore.RED}>>> {Fore.WHITE}')
        new_config['update_title'] = val.lower() in ['true', 'oui', 'o', 'yes', 'y']
    elif choice == '6':
        val = input(f'{Style.BRIGHT}{Fore.WHITE}[{Fore.BLUE}?{Fore.WHITE}] {Fore.MAGENTA}- {Fore.WHITE}Print invalid? (true/false) {Fore.RED}>>> {Fore.WHITE}')
        new_config['print_invalid'] = val.lower() in ['true', 'oui', 'o', 'yes', 'y']
    elif choice == '7':
        val = input(f'{Style.BRIGHT}{Fore.WHITE}[{Fore.BLUE}?{Fore.WHITE}] {Fore.MAGENTA}- {Fore.WHITE}Nouveau max retries {Fore.RED}>>> {Fore.WHITE}')
        if val.isdigit():
            new_config['max_retries'] = int(val)
    
    # Sauvegarder
    with open(config_path, 'w') as f:
        yaml.dump(new_config, f, default_flow_style=False)
    
    print('')
    Sprint('+', f'Configuration sauvegardée! Redémarrez le programme pour appliquer.', Fore.GREEN)
    print('')
    input(f'{Style.BRIGHT}{Fore.WHITE}[{Fore.BLUE}?{Fore.WHITE}] {Fore.MAGENTA}- {Fore.WHITE}Appuyez sur {Fore.BLUE}Entrée {Fore.WHITE}pour continuer...')

def main_menu():
    """Menu principal"""
    while True:
        show_banner()
        
        print(f'{Fore.WHITE}[{Fore.BLUE}%{Fore.WHITE}] {Fore.BLUE}- {Fore.WHITE}Configuration ->')
        print(f'{Fore.WHITE}[{Fore.BLUE}%{Fore.WHITE}] {Fore.BLUE}- {Fore.WHITE}Threads:        {Fore.BLUE}{threads_config}')
        print(f'{Fore.WHITE}[{Fore.BLUE}%{Fore.WHITE}] {Fore.BLUE}- {Fore.WHITE}Timeout:        {Fore.BLUE}{request_timeout}s')
        print(f'{Fore.WHITE}[{Fore.BLUE}%{Fore.WHITE}] {Fore.BLUE}- {Fore.WHITE}Request-Delay:  {Fore.BLUE}{request_delay}s')
        print(f'{Fore.WHITE}[{Fore.BLUE}%{Fore.WHITE}] {Fore.BLUE}- {Fore.WHITE}Test-URL:       {Fore.BLUE}{test_url}')
        print(f'{Fore.WHITE}[{Fore.BLUE}%{Fore.WHITE}] {Fore.BLUE}- {Fore.WHITE}Print-Invalid:  {Fore.BLUE}{p_inv}')
        print('')
        print(f'{Fore.WHITE}[{Fore.LIGHTCYAN_EX}@{Fore.WHITE}] {Fore.BLUE}- {Fore.WHITE}Menu Principal')
        print('')
        print(f'{Fore.WHITE}[{Fore.BLUE}1{Fore.WHITE}] {Fore.MAGENTA}- {Fore.WHITE}Générer et vérifier des proxies')
        print(f'{Fore.WHITE}[{Fore.BLUE}2{Fore.WHITE}] {Fore.MAGENTA}- {Fore.WHITE}Vérifier des proxies depuis un fichier (proxy/input/proxies.txt)')
        print(f'{Fore.WHITE}[{Fore.BLUE}3{Fore.WHITE}] {Fore.MAGENTA}- {Fore.WHITE}Modifier la configuration')
        print(f'{Fore.WHITE}[{Fore.BLUE}4{Fore.WHITE}] {Fore.MAGENTA}- {Fore.WHITE}Quitter')
        print('')
        
        choice = input(f'{Style.BRIGHT}{Fore.WHITE}[{Fore.BLUE}?{Fore.WHITE}] {Fore.MAGENTA}- {Fore.WHITE}Sélectionnez une option {Fore.RED}>>> {Fore.WHITE}')
        
        if choice == '1':
            option_generate_and_check()
        elif choice == '2':
            option_check_proxies()
        elif choice == '3':
            option_config()
        elif choice == '4':
            show_banner()
            Sprint('!', f'Au revoir!', Fore.CYAN)
            print('')
            time.sleep(1)
            sys.exit(0)
        else:
            Sprint('!', f'Option invalide!', Fore.RED)
            time.sleep(1)

if __name__ == '__main__':
    update_title('KRIX PROXY - Bienvenue')
    main_menu()
