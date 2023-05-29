from comm import kill_apps
from memcheck.memcheck import memcheck
from massif.massif import massif


color_map = {
    'red' : '\033[91m',
    'green' : '\033[92m',
    'yellow' : '\033[93m',
    'blue' : '\033[94m',
    'black' : '\033[30m',
    'default' : '\033[30m'
}


def val_print(text, color = 'default'):
    try:
        print(color_map.get(color) + text + '\033[0m')
    except (TypeError, IndexError):
        print(color_map.get('default') + text + '\033[0m')


def main():
    val_print('start valcheck.', 'green')
    memcheck()
    massif()
    val_print('valcheck done.', 'green')


if __name__ == '__main__':
    main()
