# -*- coding: UTF-8 -*-
from newf import Application, Response
from shutil import move
import pickle
import os
from jinja2 import Environment, FileSystemLoader

from mochi import get_game, list_games
from mochi.autopost import fetch_game

class Site(object):
    pass

## Setup START

PUBLISHER_ID = 'your publisher id'
mediastore = 'dir to store the media'
template_store ='./templates'

site = Site()
site.name ='Sitename'
site.media_pfx = '/static/'
site.contact_url = 'your contact (form) url'
site.slogan = 'your site slogan'

## Setup END

category_file = os.path.join(mediastore, 'categories')
env = Environment(loader=FileSystemLoader(template_store))

def render_game(game):
    template = env.get_template('game_detail.html')
    return template.render(game=game, site= site).encode('utf-8')

def render_index(game):
    template = env.get_template('index.html')
    return template.render(game=game, site= site, showabout=True).encode('utf-8')

def load_categories():
    categories = {}
    try:
        if os.path.exists(category_file):
            file = open(category_file, 'rb')
            categories = pickle.load(file)
            file.close()
    finally:
        return categories

def render_categories():
    categories = load_categories()
    template = env.get_template('game_list.html')
    return template.render(categories=categories, site= site).encode('utf-8')

def write_file(filename, content):
    path = os.path.join(mediastore, filename)
    file = open(path, 'wb')
    file.write(content)
    file.close()

def add_game(game):
    write_file(game.slug + '.html', render_game(game))    
    write_file('index.html', render_index(game))

    categories = load_categories()

    #funny, but some games do not have the category attribute
    try:
        category = game.category
    except AttributeError:
        category = game.categories[0]

    if categories.has_key(category):
        categories[category].append(game)
    else:
        list = []
        list.append(game)
        categories[category] = list

    file = open(category_file, 'wb')
    pickle.dump(categories, file, -1)
    file.close()

    write_file('list-of-all-games.html', render_categories())

def autopost(request):
    game_tag = 'None'

    if request.POST.has_key('game_tag'):
        game_tag = request.POST['game_tag'].value

    game = fetch_game(PUBLISHER_ID, game_tag, mediastore)
    add_game(game)

    return Response("ok")

def view_categories(request, **kwargs):
    return Response(render_categories())

def view_game(request, **kwargs):
    slug = kwargs['slug']
    game = get_game(mediastore, slug=slug)
    return Response(render_game(game))

def rebuild_site(request):
    games = list_games(mediastore)
    games.sort(key=lambda s: s.local_last_modifified)

    move(category_file, os.path.join(mediastore, 'categories_bak'))
    for game in games:
        add_game(game)

    return Response("done")

urls = (
    (r'^/autopost$', autopost),
    (r'^/list-of-all-games/$', view_categories),
    (r'^/rebuild/$', rebuild_site),
    (r'^/(?P<slug>.*)$', view_game),
)

application = Application(urls)

if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    server = make_server('', 8002, application)
    server.serve_forever()