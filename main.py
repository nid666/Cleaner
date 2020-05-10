import morph
import datetime
import subprocess
import os
from pywallet import wallet
from monero.wallet import Wallet
from monero.backends.jsonrpc import JSONRPCWallet

#this class allows directory changing which is needed to run the monero cli
class cd:
    """Context manager for changing the current working directory"""
    def __init__(self, newPath):
        self.newPath = os.path.expanduser(newPath)

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)

#this part creates and saves the temporary bitcoin seed incase the transaction goes wrong along with a timestamp
seed = wallet.generate_mnemonic()
tempWallet = wallet.create_wallet(network="BTC", seed=seed, children=1)
now = datetime.datetime.now()
#this creates the logfile which stores the seed and public key incase of exchange faliure
file = open("log.txt", "a")
file.write(now.strftime("%Y-%m-%d %H:%M:%S Generated Seed: "))
file.write(seed)
file.write("\n")
file.write("Refund Public Key: ")
file.write(tempWallet['address'])
file.write("\n")
file.close()
#sets morph refund address to newly generated bitcoin address
morph.refund = tempWallet['address']
#starts up the monero-cli to generate a wallet address for the exchange
with cd("monero-x86_64-linux-gnu-v0.15.0.5"):
    subprocess.call("./startwallet.sh", shell=True)
#initializes morph exchange
morph.exchange(help)
