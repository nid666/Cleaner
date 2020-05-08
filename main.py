import morph
import datetime
from pywallet import wallet
from monero.wallet import Wallet
from monero.backends.jsonrpc import JSONRPCWallet

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
#initializes morph exchange
morph.exchange(help)