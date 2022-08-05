import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

# pagination method for question
def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE
    questions = [question.format() for question in selection]
    current_questions = questions[start:end]
    return current_questions

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
  
  cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
  
  # CORS Headers
  @app.after_request
  def after_request(response):
      response.headers.add(
          "Access-Control-Allow-Headers", "Content-Type,Authorization,true"
      )
      response.headers.add(
          "Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS"
      )
      return response

  
  # endpoint to handle GET requests for all available categories.
  @app.route("/categories")
  def get_categories():
      # get all categories
      categories = Category.query.all()

      # if there is no category in database
      if categories == None:
        abort(404)
        
      # categories dict for holding the retrived categories
      categoriesDict = {}

      # adding all categories to the dict
      for category in categories:
          categoriesDict[category.id] = category.type

      return jsonify({
          'success': True,
          'categories': categoriesDict
      })




  # endpoint to handle GET requests for questions, 
  @app.route('/questions')
  def get_questions():
    # all questions ordered by id
    selection = Question.query.order_by(Question.id).all()
    # total num of questions
    totalQuestions = len(selection)
    # get current paginated questions
    currentQuestions = paginate_questions(request, selection)

    # if the page number does not exist, rise 404 error
    if (len(currentQuestions) == 0):
        abort(404)

    # get all categories
    categories = Category.query.order_by(Category.id).all()
    categoriesDict = {}
    for category in categories:
        categoriesDict[category.id] = category.type

    return jsonify({
        'success': True,
        'questions': currentQuestions,
        'totalQuestions': totalQuestions,
        'categories': categoriesDict,
        'currentCategory': None
    })
      

  # endpoint to DELETE question using a question ID. 
  @app.route('/questions/<int:id>', methods=['DELETE'])
  def delete_a_question(id):
    # retrive the question with the specified id
    question = Question.query.filter_by(id=id).one_or_none()
    # if the question is not found, rise 404 error
    if question is None:
        abort(404)

    question.delete()

    return jsonify({
        'success': True
    })


  # endpoint to POST a new question
  @app.route("/questions", methods=['POST'])
  def add_question():
    # get the body from request
    body = request.get_json()

    # get parameters of the question to be added from the request 
    newQuestion = body.get('question', None)
    newAnswer = body.get('answer', None)
    newCategory = body.get('category', None)
    newDifficulty = body.get('difficulty', None)
    search_term = body.get('searchTerm', None)

    # if the 'searchTerm' in request body is not none, get questions based on the search term
    if search_term:
        questions = Question.query.filter(
            Question.question.ilike('%'+search_term+'%')).all()
        if questions:
            currentQuestions = paginate_questions(request, questions)
            return jsonify({
                'success': True,
                'questions': currentQuestions,
                'totalQuestions': len(questions),
                'currentCategory': None
            })
        # if no question matches the search term, rise 404 error
        else:
            abort(404)
    # no 'searchTerm' in request body, add the new question
    else:
        try:
            # create a question 
            question = Question(question=newQuestion, answer=newAnswer,
                                category=newCategory, difficulty=newDifficulty)
            question.insert()
            return jsonify({
                'success': True
            })
        # if the parameters for the question to be added are invalid, rise 422 error
        except Exception as e:
            print(e)
            abort(422)

  # endpoint to get questions based on category. 
  @app.route("/categories/<int:id>/questions")
  def questions_in_a_category(id):
    # retrive the category by the given id
    category = Category.query.filter_by(id=id).one_or_none()
    if category:
        # retrive all questions of that category
        questionsInCat = Question.query.filter_by(category=str(id)).all()
        currentQuestions = paginate_questions(request, questionsInCat)

        return jsonify({
            'success': True,
            'questions': currentQuestions,
            'totalQuestions': len(questionsInCat),
            'currentCategory': category.type
        })
    # if category not found, rise 404 error
    else:
        abort(404)


  # endpoint to get questions to play the quiz. 
  @app.route('/quizzes', methods=['POST'])
  def play_quizzes():
    # get the question category and the previous questions parameters from request
    body = request.get_json()
    quizCategory = body.get('quiz_category')
    previousQuestion = body.get('previous_questions')

    # if no category is selected, retrive questions from all categories
    if (quizCategory['id'] == 0):
        questionsQuery = Question.query.all()
    # if category is selected, retrive questions from that category
    else:
        questionsQuery = Question.query.filter_by(
            category=quizCategory['id']).all()
    
    # if there is no question in that category or the category does not exist, rise 404 error
    if len(questionsQuery) == 0:
        abort(404)

    # randomization
    randomIndex = random.randint(0, len(questionsQuery)-1)
    questionToPlay = questionsQuery[randomIndex]
    
    # retrive an unplayed question
    while questionToPlay.id not in previousQuestion:
        questionToPlay = questionsQuery[randomIndex]
        return jsonify({
            'success': True,
            'question': questionToPlay.format()
        })

  #error handlers
  @app.errorhandler(400)
  def bad_request(error):
    return jsonify({
        "success": False,
        'error': 400,
        "message": "Bad request"
    }), 400

  @app.errorhandler(404)
  def page_not_found(error):
    return jsonify({
        "success": False,
        'error': 404,
        "message": "Page not found"
    }), 404

  @app.errorhandler(422)
  def unprocessable_recource(error):
    return jsonify({
        "success": False,
        'error': 422,
        "message": "Unprocessable recource"
    }), 422
   
  @app.errorhandler(405)
  def invalid_method(error):
    return jsonify({
        "success": False,
        'error': 405,
        "message": "Invalid method"
    }), 405
  
  return app

    

