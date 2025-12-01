# serial_thread.py
import threading
import serial
import time

class SerialReader(threading.Thread):
    def __init__(self, port="COM3", baud=9600):
        super().__init__()
        self.port = port
        self.baud = baud
        self.valor = 0.0
        self.running = False
        self.ser = None
        self.daemon = True  # garante que a thread morre quando o programa principal fechar

    def run(self):
        try:
            # espera o Arduino reiniciar ao abrir a porta (evita PermissionError)
            time.sleep(2.0)
            self.ser = serial.Serial(self.port, self.baud, timeout=1)
            self.running = True
            print(f"✅ Porta serial {self.port} aberta com sucesso (baud {self.baud})")
        except Exception as e:
            print(f"❌ Erro ao abrir porta serial {self.port}: {e}")
            return

        while self.running:
            try:
                linha = self.ser.readline().decode('utf-8', errors='ignore').strip()
                if not linha:
                    continue

                # aceita número com ponto decimal, opcionalmente sinal negativo
                cleaned = linha.replace('\r', '').replace('\n', '').strip()
                # permite algo como "23.45" ou "-12.3"
                if cleaned.count('.') <= 1:
                    # remove espaços e qualquer caractere não numérico exceto '.' e '-'
                    filtered = ''.join(ch for ch in cleaned if ch.isdigit() or ch in '.-')
                    if filtered and (filtered.replace('.', '', 1).replace('-', '', 1).isdigit()):
                        try:
                            self.valor = float(filtered)
                        except ValueError:
                            # ignora linhas não conversíveis
                            pass
                # se quiser logar mensagens não numéricas, descomente:
                # else:
                #     print("Mensagem não numérica recebida:", linha)

            except Exception as e:
                print("⚠️ Erro na leitura serial:", e)
                # pequena pausa para evitar flood em caso de erro contínuo
                time.sleep(0.1)

    def get_valor(self):
        return self.valor

    def stop(self):
        self.running = False
        try:
            if self.ser and self.ser.is_open:
                self.ser.close()
                print("🔌 Conexão serial encerrada.")
        except Exception as e:
            print("⚠️ Erro ao fechar serial:", e)
