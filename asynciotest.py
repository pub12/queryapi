import asyncio
import aiohttp

@asyncio.coroutine
def get(index, url):
	print ("%s running get", index)
	response = yield from aiohttp.request('GET', url)
	print ("%s got response", index)
	assert response.status == 200
	print ("%s got response ok", index)
	data = yield from response.read()
	# print ("got data:"+str(data))
	return data

# @asyncio.coroutine
def run(index, url):
	print( "%s running run", index)
	# url = 'https://api.github.com/users/caspyin'
	data= yield from get(index, url)
	print( "%s running run done", index)
	process(index, data)

def process(index, future):
	print ("running process", index)
	print( len(future ) )
	# print( len(future.result() ) )
	# loop.stop()

def addAnother():
	print( "Run SLEEP" )
	yield from asyncio.sleep( 1 )
	print("Added after SLEEP")
	asyncio.Task( run('X', 'http://www.cnn.com'))

if __name__ == '__main__':
	loop = asyncio.get_event_loop()


	# task = asyncio.Task( run('A', 'https://api.github.com/users/caspyin') )
	# task.add_done_callback( process )
	# task = asyncio.Task( run('B', 'https://maps.googleapis.com/maps/api/geocode/json?address=1600+Amphitheatre+Parkway,+Mountain+View,+CA') )
	# task.add_done_callback( process )
	# tasks = [asyncio.Task( run('A', 'https://api.github.com/users/caspyin')),
	# 		 asyncio.Task( run('B', 'https://www.yahoo.com')),
	# 		 asyncio.Task( run('C', 'https://www.fool.com')),
	# 		 asyncio.Task( run('D', 'https://maps.googleapis.com/maps/api/geocode/json?address=1600+Amphitheatre+Parkway,+Mountain+View,+CA') )]
	asyncio.Task( run('A', 'https://api.github.com/users/caspyin'))
	asyncio.Task( run('B', 'https://www.yahoo.com'))
	asyncio.Task( run('C', 'https://www.fool.com'))
	asyncio.Task( run('D', 'https://maps.googleapis.com/maps/api/geocode/json?address=1600+Amphitheatre+Parkway,+Mountain+View,+CA') )
	# url = 'http://192.168.0.104:8080/v1/node/GroveAirqualityA0/quality?access_token=bb570b0596744a60b992ca3e35a3ccd2'
	asyncio.Task( addAnother() )
	loop.run_forever()
	# loop.run_until_complete(asyncio.wait(tasks))
	# loop.run_until_complete()
	
	loop.close()