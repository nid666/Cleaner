
import datetime
import subprocess
import os
import random
import string
from pywallet import wallet
import pexpect

#this part creates and saves the temporary bitcoin seed incase the transaction goes wrong along with a timestamp
def createBtcWallet():
    seed = wallet.generate_mnemonic()
    tempWallet = wallet.create_wallet(network="BTC", seed=seed, children=1)
    now = datetime.datetime.now()
    #this creates the logfile which stores the seed and public key incase of exchange faliure
    file = open("BTClog.txt", "a")
    file.write(now.strftime("%Y-%m-%d %H:%M:%S Generated Seed: "))
    file.write(seed)
    file.write("\n")
    file.write("Refund Public Key: ")
    #this line writes the actual public address
    file.write(tempWallet['address'])
    file.write("\n")
    file.close()
    return (tempWallet['address'])

#starts up the monero-cli to generate a wallet address for the exchange
#this will use pexpect for the interaction between this script and the monero cli

#uses pex to navigate to the directory with the monero-cli
def navToFolder():
    pexpect.run('cd monero')

#generates a random string of a certain length for wallet names and passwords
def generateMoneroInfo(length):
    result_str = ''.join(random.choice(string.ascii_letters) for i in range(length))
    return(result_str)

#this starts the monero cli
def startMonero():
    child = pexpect.spawnu('./startwallet.sh')
    #this will create a new wallet with a random name
    walletName = generateMoneroInfo(4) 
    child.sendline(walletName)
    #this will set it to a random 16 digit passcode
    walletPasscode = generateMoneroInfo(16)
    child.sendline(walletPasscode)
    #this generates a temp log with these details for emergency use
    file = open("moneroLog.txt", "a")
    file.write("Name: ")
    file.write(walletName)
    file.write("\n")
    file.write("Pass: ")
    file.write(walletPasscode)


