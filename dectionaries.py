from pprint import pprint

dicionario = {'extrato': [{'Data': '13/01',
              'Descrição': 'AME DIGITAL*AME Digita',
              'Valor': '3184'},
             {'Data': '14/01',
              'Descrição': 'LINK WAP INFORMATICA',
              'Valor': '15155'},
             {'Data': '14/01',
              'Descrição': 'LOJA TAGUATINGA - DF',
              'Valor': '18110'},
             {'Data': '14/01', 'Descrição': 'BOBS', 'Valor': '1600'},
             {'Data': '14/01',
              'Descrição': 'BRASILIA PART PLANEJAM',
              'Valor': '600'},
             {'Data': '14/01',
              'Descrição': 'AME DIGITAL*AME Digita',
              'Valor': '24534'},
             {'Data': '14/01', 'Descrição': 'GULOSITOS', 'Valor': '1100'},
             {'Data': '14/01', 'Descrição': 'GULOSITOS', 'Valor': '3200'}]}

lista = []
lista2 = []
for dictio in dicionario['extrato']:
    lista.append(dictio['Data'])
    lista.append(dictio['Descrição'])
    lista.append(dictio['Valor'])
    lista2.append(lista)
    lista = []
print(lista2)
