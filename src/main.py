import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt

from namelist import *
from classes import *

#===============================================================================
nplayers = 3        # How many players?
nturn = 1000        # How many turns for each simulation?
nsimu = 10          # How many simulations?

wins = { i+1:0 for i in range(nplayers)}

for isim in range(1,nsimu+1):

    # Initialize the board and players
    board = Board()
    players = { 1: Player('Haiyang', jail_pay_strategy=0, cash_hold=100, sell_strategy=1), 
                2: Player('Jackie', jail_pay_strategy=1, cash_hold=200, sell_strategy=1), 
                3: Player('Becca', jail_pay_strategy=2, cash_hold=300, sell_strategy=0)}

    # File name of the output information
    fname_output = './output/record_simu'+format(isim,'04')+'.txt'
    fout = open(fname_output, 'w')

    # Players' basic information
    for i in players.keys():
        players[i].printinf(fout, board)

    # Start the game
    for i in range(nturn):
        fout.write('----------------------------- Turn '+format(i+1)+' -----------------------------\n')
        for i in players.keys():
            players[i].roll(fout, board, players)
    fout.close()

    # Check who wins
    maxcash = 0
    winnerid = 0
    for i in players.keys():
        if maxcash < players[i].cash:
            maxcash = players[i].cash
            winnerid = i
    if winnerid > 0:  
        wins[winnerid] += 1
    print 'Simulation: ', isim, ', ', players[winnerid].name, ' wins!'

    # Plot the evolution of each player's cash
    cstrs = ['r','g','b','m','c','y','k']
    plt.figure(1, figsize=(8, 5))
    k = 0
    for i in players.keys():
        plt.plot(players[i].history_cash, cstrs[k], lw=2)
        k += 1
    plt.legend([ players[i].name  for i in players.keys()], loc=2)
    plt.title('Simulation '+format(isim))
    plt.xlabel('Rolls')
    plt.ylabel('Cash ($)')
    plt.tight_layout()
    ffig = './output/figure_simu'+format(isim,'04')+'.png'
    plt.savefig(ffig)
    plt.close(1)

print '--------------------------------------------------------------------------'
print [players[i].name+' wins '+format(wins[i])+' times' for i in players.keys()]

