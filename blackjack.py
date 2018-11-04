import json
import os

# taken from: http://code.activestate.com/recipes/578231-probably-the-fastest-memoization-decorator-in-the-/
def memodict(f):
    """ Memoization decorator for a function taking a single argument """
    class memodict(dict):
        def __missing__(self, key):
            ret = self[key] = f(key)
            return ret 
    return memodict().__getitem__


@memodict
def getDeck(played_cards):
	deck = [None,0,4,4,4,4,4,4,4,4,16,4]	
	for card in played_cards:
		deck[card] -= 1
	deck[11] += deck[1]
	deck[1] = None
	return deck


@memodict
def calcDealer(cards):
	# playerCards should be pre-sorted
	playerCards, upCards = cards
	deckCards = getDeck(tuple(sorted(upCards+playerCards)))
	deckSize = sum(deckCards[2:])
	upTotal = sum(upCards)
	
	if upTotal > 21:
		if (11 in upCards):
			# ace
			upCardsList = list(upCards)
			upCardsList[upCardsList.index(11)] = 1
			upCards = tuple(upCardsList)
			upTotal = sum(upCards)
		else:
			# bust
			return (1,0,0,0,0,0)
	# print(str(sum(upCards))+" "+str(upCards))
	if upTotal < 17:
		retProb = [0,0,0,0,0,0]
		for i in range(2,12):
			if (deckCards[i] > 0):
				partProb = calcDealer( (playerCards, tuple(sorted(upCards+(i,)))) )
				prob = float(deckCards[i])/deckSize
				scaledProb = [a*prob for a in partProb]
				# retProb = [sum(x) for x in zip(retProb, scaledProb)]
				retProb[0] += scaledProb[0]
				retProb[1] += scaledProb[1]
				retProb[2] += scaledProb[2]
				retProb[3] += scaledProb[3]
				retProb[4] += scaledProb[4]
				retProb[5] += scaledProb[5]
		return retProb
	elif upTotal == 17:
		return (0,1,0,0,0,0)
	elif upTotal == 18:
		return (0,0,1,0,0,0)
	elif upTotal == 19:
		return (0,0,0,1,0,0)
	elif upTotal == 20:
		return (0,0,0,0,1,0)
	elif upTotal == 21:
		return (0,0,0,0,0,1)


@memodict
def stand(cards):
	playerCards, dealerCards = cards

	playerTotal = sum(playerCards)
	if (playerTotal > 21) and (11 in playerCards):
		playerCardsList = list(playerCards)
		playerCardsList[playerCardsList.index(11)] = 1
		playerCards = tuple(playerCardsList)
		playerTotal = sum(playerCards)

	tot = calcDealer( (tuple(sorted(playerCards)), dealerCards) )

	if playerTotal < 17:
		return (tot[0],0,sum(tot[1:]))
	if playerTotal == 17:
		return (tot[0],tot[1],sum(tot[2:]))
	if playerTotal == 18:
		return (sum(tot[:2]),tot[2],sum(tot[3:]))
	if playerTotal == 19:
		return (sum(tot[:3]),tot[3],sum(tot[4:]))
	if playerTotal == 20:
		return (sum(tot[:4]),tot[4],sum(tot[5:]))
	if playerTotal == 21:
		return (sum(tot[:5]),tot[5],0)
	if playerTotal > 21:
		return (0,tot[0],sum(tot[1:]))


@memodict
def hit(cards):
	# returns [win_count,tie_count,lose_count]
	# print(str(sum(playerCards)) + " " + str(playerCards))
	playerCards, dealerCards = cards
	deck = getDeck( tuple(sorted(dealerCards+playerCards)) )
	deckSize = sum(deck[2:])
	retProb = [0,0,0,0,0,0]
	for i in range(2,12):
		if (deck[i] == 0):
			continue;
		best_prob = None
		if sum(playerCards+(i,))>21:
			if (11 in playerCards+(i,)):
				# ace
				tempCards = playerCards+(i,)
				tempCardsList = list(tempCards)
				tempCardsList[tempCardsList.index(11)] = 1
				tempCards = tuple(tempCardsList)
				hit_prob = hit( (tuple(sorted(tempCards)), dealerCards) )
				stand_prob = stand( (tuple(sorted(tempCards)), dealerCards) )

				if hit_prob[0]/(hit_prob[0]+hit_prob[2]) > stand_prob[0]/(stand_prob[0]+stand_prob[2]):
					best_prob = hit_prob
				else:
					best_prob = stand_prob
			else:
				# bust
				best_prob = stand( (tuple(sorted(playerCards+(i,))), dealerCards) )
		elif sum(playerCards+(i,))==21:
			best_prob = stand( (tuple(sorted(playerCards+(i,))), dealerCards) )
		else:
			hit_prob = hit( (tuple(sorted(playerCards+(i,))), dealerCards) )
			stand_prob = stand( (tuple(sorted(playerCards+(i,))), dealerCards) )

			if hit_prob[0] > stand_prob[0]:
				best_prob = hit_prob
			else:
				best_prob = stand_prob
			
		# integrate with the rest of the possibilities
		prob = float(deck[i])/deckSize
		scaledProb = [a*prob for a in best_prob]
		retProb = [sum(x) for x in zip(retProb, scaledProb)]
	return retProb


# main code starts here
if os.path.isfile('raw.json'):
	with open("raw.json",'r') as fp:
		print("Using intermediate calculations from "+fp.name+"...")
		probList = json.load(fp)
else:
	print("Regenerating intermediate calculations...")
	probList = []
	for d_i in range(2,12):
		for p_i in range(2,12):
			for p_j in range(p_i,12):
				cards = ( tuple(sorted((p_i,p_j))),(d_i,) )
				hit_prob = hit( cards )
				stand_prob = stand( cards )
				print("cards: {}, hit: {}, stand: {}".format(cards, hit_prob, stand_prob))
				probList.append( (cards, hit_prob, stand_prob) )
	
	# save to file
	with open("raw.json","w") as fp:
		print("Saving to "+fp.name)
		json.dump(probList, fp)

	# save pretty version for easier reading by humans
	with open("raw_pretty.json","w") as fp:
		print("Saving pretty output to "+fp.name)
		probListPretty = []
		for i in probList:
			probListPretty.append(
				{
					"cards": {
						"player": i[0][0],
						"dealer": i[0][1],
					},
					"probs": {	
						"hit": {
							"win": i[1][0],
							"tie": i[1][1],
							"lose": i[1][2]
						},
						"stand": {
							"win": i[2][0],
							"tie": i[2][1],
							"lose": i[2][2]
						}
					}
				})
		json.dumps(probListPretty, fp, sort_keys=True, indent=2)


accum = 0

# add up all probabilities
for d_i in range(2,12):
	for p_i in range(2,12):
		for p_j in range(2,12):
			for (cards, hit, stand) in probList:
				if (tuple(sorted(cards[0])),tuple(cards[1])) == (tuple(sorted((p_i,p_j))),(d_i,)):
					seen_list = []

					if p_i == 10:
						p_i_prob = 16
					else:
						p_i_prob = 4

					seen_list.append(p_i)

					if p_j == 10:
						p_j_prob = 16-seen_list.count(p_j)
					else:
						p_j_prob = 4-seen_list.count(p_j)
					
					seen_list.append(p_j)

					if d_i == 10:
						d_i_prob = 16-seen_list.count(d_i)
					else:
						d_i_prob = 4-seen_list.count(d_i)

					prob = (p_i_prob*p_j_prob*d_i_prob) / (52*51*50)

					hit_payout = (2*hit[0])+hit[1]
					stand_payout = (2*stand[0])+stand[1]
					if hit_payout > stand_payout:
						best_payout = hit_payout
					else:
						best_payout = stand_payout

					accum += best_payout * prob	

print(accum)