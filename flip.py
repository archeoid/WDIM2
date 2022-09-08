import random

async def flip_coin(request):
  result = random.randint(0,1)
  if result == 0:
    output = "heads"
  elif result == 1:
    output = "tails"
    
  return f"You flipped a coin! It landed {output} side up"
