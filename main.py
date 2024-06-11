from flask                          import Flask

from website.views                  import views

def create_app() :
    app = Flask(__name__, template_folder='website/templates', static_folder='website/static')
    app.config['SECRET_KEY'] = 'mamamo'

    app.register_blueprint(views, url_prefix='/')

    return app

if __name__ == '__main__' :
    create_app().run(debug=True)
