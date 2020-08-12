import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category, db

QUESTIONS_PER_PAGE = 10


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

    def paginate_result(request, data):
        page = request.args.get("page", 1)
        start = (int(page) - 1) * 10
        end = start + 10

        return data[start:end]

    @app.after_request
    def after_request(response):
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization,true"
        )
        response.headers.add(
            "Access-Control-Allow-Methods", "GET,PATCH,POST,DELETE,OPTIONS"
        )
        return response

    @app.route("/categories", methods=["GET"])
    def get_catagories():
        categories = Category.query.all()
        formatted_categories = [category.format() for category in categories]
        categories = {}
        for category in formatted_categories:
            categories[str(category["id"])] = category["type"]
        return jsonify({"success": True, "categories": categories})

    @app.route("/questions", methods=["GET"])
    def get_questions():
        result = (
            db.session.query(Question, Category)
            .filter(Question.category == Category.id)
            .all()
        )

        if not result:
            abort(500)

        # format and paginate questions
        questions = [question for question, _ in result]
        formatted_questions = [question.format() for question in questions]
        paginated_questions = paginate_result(request, formatted_questions)

        # get all categories of the questions
        categories = {category for _, category in result}
        formatted_categories = [category.format() for category in categories]

        # format them to be dict
        categories_dict = {}
        for category in formatted_categories:
            app.logger.info(category)
            categories_dict[str(category["id"])] = category["type"]

        if len(categories) == 1:
            current_category = categories_dict.values()[0]
        else:
            current_category = list(categories_dict.values())

        return jsonify(
            {
                "success": True,
                "questions": paginated_questions,
                "categories": categories_dict,
                "total_num_questions": len(questions),
                "current_category": current_category,
            }
        )

    @app.route("/questions/<int:question_id>", methods=["DELETE"])
    def delete_question(question_id):
        try:
            question = Question.query.get(question_id)
            question.delete()
        except Exception:
            db.session.rollback()
            abort(404)
        finally:
            db.session.close()

        return jsonify({
            "success": True,
            "message": "Question {} deleted".format(question_id)}
        )

    @app.route("/questions", methods=["POST"])
    def create_question():
        try:
            data = request.get_json()
            question_text = data["question"]
            answer = data["answer"]
            difficulty = data["difficulty"]
            category = data["category"]

            question = Question(
                question=question_text,
                answer=answer,
                difficulty=difficulty,
                category=category,
            )
            question.insert()
        except Exception:
            db.session.rollback()
            abort(422)
        finally:
            db.session.close()
        return jsonify({
            "success": True,
            "message": "question was successfely added"
        })

    @app.route("/questions/search", methods=["POST"])
    def search_questions():
        search = request.get_json().get("query", "")
        look_for = "%{0}%".format(search)
        result = Question.query.filter(Question.question.ilike(look_for)).all()

        if not result:
            abort(404)

        formatted_questions = [question.format() for question in result]
        paginated_questions = paginate_result(request, formatted_questions)

        return jsonify(
            {
                "success": True,
                "questions": paginated_questions,
                "total_num_questions": len(result),
            }
        )

    @app.route("/categories/<int:category_id>/questions", methods=["GET"])
    def get_question_per_category(category_id):
        category = Category.query.get(category_id)

        if not category:
            abort(500)

        result = Question.query.filter(Question.category == category_id).all()

        if not result:
            abort(500)

        formatted_questions = [question.format() for question in result]
        paginated_questions = paginate_result(request, formatted_questions)

        return jsonify(
            {
                "success": True,
                "questions": paginated_questions,
                "total_num_questions": len(result),
                "category": category.type,
            }
        )

    @app.route("/quizzes", methods=["POST"])
    def quiz_questions():
        data = request.get_json()
        quiz_category = data.get("quiz_category", {"id": 1})
        category_id = quiz_category["id"]
        previous_questions = data.get("previous_questions", [])

        if category_id == 0:
            result = Question.query.all()
        else:
            result = (
                Question.query.filter(Question.category == category_id)
                .filter(~Question.id.in_(previous_questions))
                .all()
            )

        if not result:
            return jsonify({
                "success": True,
                "previous_questions": previous_questions
            })

        random_id = random.randint(0, len(result) - 1)
        formatted_question = result[random_id].format()
        previous_questions.append(formatted_question['id'])

        return jsonify({
            "success": True,
            "question": formatted_question,
            "previous_questions": previous_questions
        })

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404, "message": "Not Found"
        }), 404

    @app.errorhandler(422)
    def unprocessabel(error):
        return (jsonify({
            "success": False,
            "error": 422,
            "message": "Unprocessable"}),
            422,
        )

    @app.errorhandler(500)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 500,
            "message": "Something Went Wrong"
        }), 500

    return app
