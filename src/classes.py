import numpy as np
import pandas as pd
from namelist import *


class Board:
    def __init__(self, fn=fname_board):
        board=pd.read_csv(fn)
        self.properties = []    # List of tiles
        self.tilepos = []       # Tile position
        for i in range(len(board.name)):
            self.properties.append( Property(name=board.name[i], 
                                        group=board.group[i], 
                                        color=board.color[i], 
                                        position=board.position[i], 
                                        prices=[board.price_buy[i], board.price_build[i]], 
                                        rents=[board.rent[i], board.rent_build_1[i], board.rent_build_2[i], 
                                               board.rent_build_3[i], board.rent_build_4[i], board.rent_build_5[i]], 
                                        monopolysize=board.size_monopoly[i] ) )
            if self.properties[-1].name == 'Jail': 
                self.jail_position = self.properties[-1].position
            if self.properties[-1].name == 'Go To Jail': 
                self.gotojail_position = self.properties[-1].position
            self.tilepos.append(self.properties[-1].position)
        self.total_tile = len(self.properties)      # How many tiles totally
        return

                
class Property:
    def __init__(self, name='Go', group='Idle', color=None, 
                 position=0, prices=[0,0], rents=[0]*6, monopolysize=0):
        self.name  = name                   # Property name
        self.group = group                  # Group
        self.color = color                  # Color
        self.position = position            # Board position
        self.prices = prices                # Price to [0]buy and [1]built
        self.rents = rents                  # Rents: [0: basic rent, 1: with one house, 2: with two houses, ...
                                            #       , 5: with one hotel]
        self.msize = monopolysize           # How many tiles with the same color/group to get monopoly

        self.house = 0                      # How many houses have been built?
        self.owner = None                   # Owner of this property
        self.mortgage = False               # Mortgage status
        self.monopoly = False               # Is this tile monopoly or not?
        return

    
class Player:
    '''
    jail_pay_strategy
        0: pay the fee directly; 
        1: roll once; 
        2: roll twice

    cash_hold: The minimum cash one wants to hold.

    sell_strategy
        0: once one uses up the cash, sell all the houses and properties;
        1: sell the house first, then properties one by one from the list, until one has enough cash
        
    buy_strategy
        0: if one lands on a new tile, buy that tile if he/she has enough cash
    
    '''
    def __init__(self, name=None, jail_pay_strategy=0, cash_hold=0, sell_strategy=0, buy_strategy=0):
        self.name = name                    # Player's name (ID)
        self.cash = init_cash               # Cash on hand
        self.jail_pay = jail_pay_strategy
        self.cash_hold = cash_hold
        self.sell_strategy = sell_strategy
        self.buy_strategy = buy_strategy
        self.properties = []                # List of owned properties
        self.position = 0                   # Position on the board
        self.jail_cards  = 0                # Number of "Get Out Of Jail Free" cards
        self.jail_turns  = 0                # Number of remaining turns in jail
        self.doublerolls = 0                # Number of "double rolls"

        self.bankrupt = False               # Bankrupt or not
        self.history_position  = [0]        # History of positions on the board
        self.history_cash  = [self.cash]    # History of cash of every roll
        self.history_property  = [ self.properties ]    # History of owned properties
        return

    def printinf(self, fid, board):
        # Output the players' information to the file
        fid.write('    Player: '+self.name+', bankrupt = '+format(self.bankrupt) +', cash = '+format(self.cash)+'\n')
        pp = board.properties[board.tilepos.index(self.position)]
        fid.write('    position: '+pp.name+'  '+format(pp.position)+'  (Jail_Num='+format(self.jail_turns)+')\n')
        fid.write('    properties: ('+format(len(self.properties))+') \n')
        for i in range(len(self.properties)):
            fid.write('    '*2+self.properties[i].name+ \
                      ' (H='+format(self.properties[i].house)+') '+self.properties[i].color+' \n')
        return

    def selling(self):
        # Sell houses or properties
        if len(self.properties)>0:
            if self.sell_strategy == 0:
                for pp in self.properties[::-1]:
                    if pp.mortgage:
                        continue
                    else:
                        self.cash += int(pp.prices[0]/2) + int(pp.prices[1]*pp.house/2)
                    pp.house = 0
                    pp.owner = None
                    pp.mortgage = False
                    pp.monopoly = False
                self.properties = []
            if self.sell_strategy == 1:
                for pp in self.properties[::-1]:
                    if pp.mortgage:
                        self.cash += int(pp.prices[0]/2)
                        pp.house = 0
                        pp.owner = None
                        pp.mortgage = False
                        pp.monopoly = False
                        self.properties.pop()
                        self.update_monopoly(pp)
                        if self.cash > self.cash_hold:  return
                    else:
                        if pp.house > 0:
                            for i in range(pp.house):
                                self.cash += int(pp.prices[1]/2)
                                pp.house -= 1
                                if self.cash > self.cash_hold:  return
                        self.cash += int(pp.prices[0]/2)
                        pp.mortgage = True
                        if self.cash > self.cash_hold:  return
            return

    def buying(self, pp):
        # Buy properties or build houses
        ppexist = False
        for ps in self.properties:
            if pp.name == ps.name:
                ppexist = True
        if ppexist:
            if pp.mortgage and self.cash-self.cash_hold >= int(pp.prices[0]/2*(1+mortgage_rate)):
                self.cash -= int(pp.prices[0]/2*(1+mortgage_rate))
                pp.mortgage = False
                self.update_monopoly(pp)
            if ~pp.mortgage and pp.monopoly and pp.house < 5 and self.cash-self.cash_hold >= pp.prices[1]:
                self.cash -= pp.prices[1]
                pp.house += 1
        else:
            if pp.owner == None and self.cash-self.cash_hold >= pp.prices[0]:
                self.cash -= pp.prices[0]
                self.properties.append(pp)
                pp.owner = self.name
                self.update_monopoly(pp)
        return
        
    def update_monopoly(self, pp):
        # Check if any property becomes monopoly
        if pp.group in ['Street', 'Railroad', 'Utility']:
            ps = []
            for p2 in self.properties:
                if p2.group == pp.group and p2.color == pp.color: ps.append(p2)
            if len(ps) >= pp.msize:
                for p2 in ps:  p2.monopoly = True
            else:
                for p2 in ps:  p2.monopoly = False
        return
                
    def roll(self, fid, board, players):
        # Roll the dices, move, and interact with the property that the player lands on
        if self.bankrupt:
            return
        else:
            d = np.random.choice(dice_choices, dice_num, dice_p)
            s = '  '; 
            for i in d: 
                s += format(i)+'  '
            fid.write(self.name + s + ', sum = '+format(np.sum(d)) +', doublerolls = '+format(self.doublerolls)+'\n')

            if self.position == board.jail_position and self.jail_turns > 0:
                if (self.jail_pay + self.jail_turns) == 3:
                    self.cash -= jail_payment
                    self.jail_turns = 0
                    if self.cash-self.cash_hold < 0:
                        self.selling()
                        if self.cash-self.cash_hold < 0: self.bankrupt = True
                else:
                    self.jail_turns -= 1
                    if d[0] == d[1]:
                        self.jail_turns = 0
                        self.position += np.sum(d)
                    d *= 0
            
            self.position += np.sum(d)

            if self.position == board.gotojail_position:
                fid.write('====> go to jail \n')
                self.doublerools = 0
                d *= 0
                self.jail_turns = 3
                self.position = board.jail_position

            if self.position >= board.total_tile:
                self.position -= board.total_tile
                self.cash += passing_cash

            # interaction with the property
            tilepos = board.tilepos[self.position]
            pp = board.properties[tilepos]
            if pp.group in ['Street', 'Railroad', 'Utility']:
                if pp.owner == None or pp.owner == self.name:
                    self.buying(pp)
                else:
                    if pp.house > 0 and pp.group == 'Street': 
                        rent = pp.rents[pp.house]
                    else:
                        if pp.monopoly:
                            rent = pp.rents[0]*2
                        else:
                            rent = pp.rents[0]
                    self.cash -= rent
                    for i in players.keys():
                        if players[i].name == pp.owner:
                            players[i].cash += rent
                        
            if pp.group in ['Tax']:
                if pp.name == 'Income Tax':
                    if pp.prices[0] >= int( self.cash * taxrate):
                        self.cash -= int(self.cash * taxrate)
                    else:
                        self.cash -= pp.prices[0]
                if pp.name == 'Luxury Tax':
                    self.cash -= pp.prices[0]

            if self.cash - self.cash_hold < 0:
                self.selling()
                if self.cash - self.cash_hold < 0: self.bankrupt = True

            self.printinf(fid, board)
            
            if d[0] == d[1] and np.sum(d)>0: 
                if self.doublerolls < 3:
                    self.doublerolls += 1
                    self.roll(fid, board, players)
                else:
                    self.position = board.jail_position

            self.doublerolls = 0
            self.history_position.append(self.position)
            self.history_cash.append(self.cash)            
            return


