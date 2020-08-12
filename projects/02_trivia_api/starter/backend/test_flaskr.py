import os
import unittest
import json
from flask_sqlalchemy import SQLAlchemy

from flaskr import create_app
from models import setup_db, Question, Category, db


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        self.database_name = "trivia_test"
        self.database_path = "postgres://{}/{}".format(
            "localhost:5432", self.database_name
        )
        setup_db(self.app, self.database_path)

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()

    def tearDown(self):
        """Executed after reach test"""
        pass

    def test_get_categories(self):
        res = self.client().get("/categories")
        date = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(date["success"], True)

    def test_fail_get_categories(self):
        res = self.client().post("/categories")

        self.assertEqual(res.status_code, 405)
        self.assertEqual(res.status, '405 METHOD NOT ALLOWED')

    def test_get_questions(self):
        res = self.client().get("/questions")
        data = json.loads(res.data)

        questions = Question.query.all()
        categories_ids = list({question.category for question in questions})
        categories = (
            db.session.query(Category)
            .filter(Category.id.in_(categories_ids)).all()
        )
        categories_dict = {}
        for category in categories:
            categories_dict[str(category.id)] = category.type

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertEqual(data["total_num_questions"], len(questions))
        self.assertCountEqual(data["categories"], categories_dict)
        self.assertCountEqual(
            data["current_category"], list(categories_dict.values()))
        self.assertEqual(len(data["questions"]), 10)

    def test_fail_get_questions(self):
        res = self.client().put("/questions")

        self.assertEqual(res.status_code, 405)
        self.assertEqual(res.status, '405 METHOD NOT ALLOWED')

    def test_delete_question(self):
        res = self.client().delete("/questions/2")
        data = json.loads(res.data)
        # test that this record is no longer in the db
        question = Question.query.get(2)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertEqual(data["message"], "Question 2 deleted")
        self.assertEqual(question, None)

    def test_fail_delete_question(self):
        # test to delete non-existing question
        res = self.client().delete("/questions/1")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "Not Found")

    def test_create_question(self):
        question_data = {
            "question": "how are you",
            "answer": "good",
            "difficulty": 3,
            "category": 2,
        }
        res = self.client().post("/questions", json=question_data)
        data = json.loads(res.data)
        # check if the question is in the db
        new_question = Question.query.filter(
            Question.question == question_data["question"]
        ).first()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertEqual(data["message"], "question was successfely added")
        self.assertEqual(new_question.question, question_data["question"])
        self.assertEqual(new_question.answer, question_data["answer"])
        self.assertEqual(new_question.difficulty, question_data["difficulty"])
        self.assertEqual(new_question.category, question_data["category"])

    def test_fail_create_question(self):
        # try add a courrpt question, missing category
        question_data1 = {
            "question": "not eligable question",
            "answer": "good",
            "difficulty": 3,
        }

        res = self.client().post("/questions", json=question_data1)

        data = json.loads(res.data)
        # check if the question is in the db
        new_question1 = Question.query.filter(
            Question.question == question_data1["question"]
        ).first()

        self.assertEqual(res.status_code, 422)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "Unprocessable")
        self.assertEqual(new_question1, None)

    def test_search_question(self):
        res = self.client().post("/questions/search", json={"query": "title"})
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertEqual(data["total_num_questions"], 2)

    def test_fail_search_question(self):
        res = self.client().get("/questions/search?query='mmm'")
        self.assertEqual(res.status_code, 405)
        self.assertEqual(res.status, '405 METHOD NOT ALLOWED')

        res = self.client().post("/questions/search", json={"query": "mmmm"})
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "Not Found")

    def test_get_questions_per_category(self):
        res = self.client().get("/categories/1/questions")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertEqual(data["total_num_questions"], 3)

    def test_fail_get_questions_per_category(self):
        # non existing category
        res = self.client().get("/categories/7/questions")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 500)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "Something Went Wrong")

    def test_quiz(self):
        res = self.client().post(
            "/quizzes",
            json={
                "quiz_category": {"type": "art", "id": 2},
                "previous_questions": [16],
            },
        )
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertEqual(
            data["previous_questions"], [16, data['question']['id']])

        res = self.client().post(
            "/quizzes",
            json={
                "quiz_category": {"type": "Science", "id": 1},
                "previous_questions": [20, 21, 22],
            },
        )
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertEqual(data["previous_questions"], [20, 21, 22])

    def test_fail_quiz(self):
        res = self.client().get("/quizzes",)
        self.assertEqual(res.status_code, 405)
        self.assertEqual(res.status, '405 METHOD NOT ALLOWED')

        # non-existed category
        res = self.client().post(
            "/quizzes",
            json={
                "quiz_category": {"type": "Science", "id": 9},
                "previous_questions": [],
            },
        )
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertEqual(data["previous_questions"], [])


# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()
