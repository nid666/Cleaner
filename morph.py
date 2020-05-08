import re
import json
import argparse
from sys import argv
from urllib.request import Request, urlopen
from urllib.error import HTTPError

SUPPORTED_CURRENCIES = ["BTC", "LTC", "ETH", "BCH", "DASH", "XMR"]
global refund
ADDRESS_VALIDATION_REGEX = {
    "BTC": "^(bc1|[13])[a-zA-HJ-NP-Z0-9]{25,39}$",
    "LTC": "^[LM3][a-km-zA-HJ-NP-Z1-9]{26,33}$",
    "ETH": "0x[a-fA-F0-9]{40}",
    "BCH": "[13][a-km-zA-HJ-NP-Z1-9]{33}",
    "DASH": "^X[1-9A-HJ-NP-Za-km-z]{33}$",
    "XMR": "^(4|8)[1-9A-HJ-NP-Za-km-z]{94}([1-9A-HJ-NP-Za-km-z]{11})?$"
}


def format_amount(asset, amount):
    if asset == "ETH":
        amount /= 10**18
    elif asset == "XMR":
        amount /= 10**12
    else:
        amount /= 10**8

    return "{:.8f}".format(amount)


def display_trade(result):
    print("\nhttps://morphtoken.com/morph/view?q={} [Requires JavaScript]".format(result['id']))
    print("Your morphtoken id: {}\n".format(result['id']))
    print("------------ {} ------------\n".format(result['state'] if not (result['state'] == "COMPLETE"
                                                                      and result['output'][0]['txid'] is None)
                                                  else 'SENDING'))
    if result['state'] == "PENDING":
        print("Waiting for a deposit, send {} to {}".format(result['input']['asset'],
                                                            result['input']['deposit_address']))
        print("Rate: {} {} <- 1 {}\n".format(result['output'][0]['seen_rate'],
                                             result['output'][0]['asset'],
                                             result['input']['asset']))
        print("Limits:")
        print("  Minimum amount accepted: {} {}".format(format_amount(result['input']['asset'],
                                                        result['input']['limits']['min']),
                                                        result['input']['asset']))
        print("  Maximum amount accepted: {} {}".format(format_amount(result['input']['asset'],
                                                        result['input']['limits']['max']),
                                                        result['input']['asset']))
        print("\nSend a single deposit. If the amount is outside the limits, a refund will happen.")
    elif result['state'] in ["PROCESSING", "TRADING", "CONFIRMING"]:
        if result['state'] == 'CONFIRMING':
            print("Waiting for confirmations")
        elif result['state'] == 'TRADING':
            print("Your transaction has been received and is confirmed. Morph is now executing your trade.\n"
                  "Usually this step takes no longer than a minute, "
                  "but there have been reports of it taking a couple of hours.\n"
                  "Wait a bit before contacting support.")
        print("Converting {} to {}".format(result['input']['asset'], result['output'][0]['asset']))
        print("Sending to {}".format(result['output'][0]['address']))
        print("\nStuck? Contact support at contact@morphtoken.com")
    elif result['state'] == "COMPLETE":
        output = result['output'][0]
        if output['txid'] is None:
            print("Morphtoken is sending your transaction.\n")
            if output['asset'].upper() == 'XMR':
                print("Note from Morphtoken: Regarding XMR withdrawals taking longer, "
                      "it's something we're trying to figure out how to handle better. "
                      "Volume is increasing and due to security measures we don't keep "
                      "too much in our hot wallet, and sometimes no one is around to "
                      "manually move funds to it. This doesn't have to do with specific "
                      "trades, it's just operational issues that we're dealing with.\n")

            print("Morphtoken will send {} {} to {}".format(format_amount(output['asset'],
                                                            output['converted_amount'] - output['network_fee']['fee']),
                                                            output['asset'],
                                                            output['address']))
        else:
            print("Sent {} {} to {}\ntxid: {}".format(format_amount(output['asset'],
                                                  output['converted_amount'] - output['network_fee']['fee']),
                                                  output['asset'],
                                                  output['address'],
                                                  output['txid']))
    elif result['state'] in ["PROCESSING_REFUND", "COMPLETE_WITH_REFUND"]:
        print("Morphtoken will refund {} {}\nReason: {}".format(result['final_amount'],
                                                                result['asset'],
                                                                result['reason']))
        if result.get('txid'):
            print("txid: {}".format(result['txid']))
    elif result['state'] == "COMPLETE_WITHOUT_REFUND":
        print("Deposit amount below network fee, too small to refund.")
    print("\n------------------------" + "-"*(2 + len(result['state'])))


def view(args):
    if not args.id:
        args.id = input("Morphtoken ID or morphtoken deposit address: ")

    try:
        r = urlopen('https://api.morphtoken.com/morph/' + args.id)
    except HTTPError as e:
        print(e)
        if e.reason == "NOT FOUND":
            print("Trade not found.")
        else:
            print("Failed to load trade")
        exit(1)
    else:
        result = json.loads(r.read().decode('utf-8'))

        display_trade(result)


def user_continue(string):
    if not input(string + ' [y/n]: ').strip().lower().startswith('y'):
        exit(1)


def check_currency_supported(currency):
    if currency not in SUPPORTED_CURRENCIES:
        user_continue("The currency you entered may not be supported by Morphtoken.\n"
                      "Are you sure you want to continue?")


def validate_address(address, currency):
    try:
        pattern = ADDRESS_VALIDATION_REGEX[currency]
    except KeyError:
        return

    if not re.match(pattern, address):
        user_continue("The address you entered may not be a valid {} address.\n"
                      "Are you sure you want to continue?".format(currency))


def exchange(args):
    input_curr = "BTC"
    check_currency_supported(input_curr)

    output_curr = "XMR"
    check_currency_supported(output_curr)
    validate_address(refund, input_curr)
    address = input("destination address: ").strip()
    if not address:
        print("error: please enter a destination address")
        exit(1)
    validate_address(address, output_curr)

    req = Request(
        'https://api.morphtoken.com/morph',
        json.dumps({
            'input': {
                'asset': input_curr,
                'refund': refund
            },
            'output': [{
                'asset': output_curr,
                'weight': 10000,
                'address': address
            }]
        }).encode('utf8'),
        {'Content-Type': 'application/json'}
    )

    try:
        resp = urlopen(req)
    except HTTPError as e:
        print('\n' + str(e))
        if e.reason == "BAD REQUEST" or e.reason == "BAD GATEWAY":
            print(json.loads(e.read().decode('utf8'))['description'])
        elif e.reason == "FORBIDDEN":
            print('Morphtoken blocks US-based exit nodes.\n'
                  'Manually change your exit node or wait a couple minutes for it to change automatically.\n'
                  'Tails users: if have an admin password set you can change your exit node with:\n'
                  'echo ExitNodes "{de}" | sudo tee -a /etc/tor/torrc && systemctl restart tor')
        exit(1)
    else:
        result = json.loads(resp.read().decode('utf8'))
        resp.close()

        display_trade(result)

        user_continue("Save Morphtoken ID to file?")
        with open('morphid.txt', 'a') as f:
            f.write(result['id'] + '\n')
        print("Morphtoken ID saved to 'morphid.txt'")


def rates(args):
    req = Request(
        'https://api.morphtoken.com/rates'
    )

    resp = urlopen(req)
    result = json.loads(resp.read().decode('utf8'))
    resp.close()

    keys = sorted(result['data'])
    max_key_length = max(len(s) for s in keys)

    print("|{}".format(' '*(max_key_length + 2)), end="|")
    for key in keys:
        print(key.center(10, " "), end="|")
    print()

    for key in keys:
        print("|{}".format(key.center(max_key_length + 2)), end="|")
        for s in keys:
            if s == key:
                print("1 ".rjust(10), end="|")
            else:
                print("{:8.5f}".format(float(result['data'][key][s])).center(10, " "), end="|")
        print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='torsocks python3 morphscript.py')
    subparsers = parser.add_subparsers()

    parser_rates = subparsers.add_parser('rates', help='Get all instant rates')
    parser_rates.set_defaults(func=rates)

    parser_view = subparsers.add_parser('view', help='Fetch an existing trade')
    parser_view.add_argument('--id', type=str, help='Morph trade to lookup, pass its id or the deposit address')
    parser_view.set_defaults(func=view)

    parser_exchange = subparsers.add_parser('exchange', help='Exchange one coin for another')
    parser_exchange.set_defaults(func=exchange)

    parser_args = parser.parse_args()
    if argv[1:]:
        parser_args.func(parser_args)
    else:
        exchange(parser_args)