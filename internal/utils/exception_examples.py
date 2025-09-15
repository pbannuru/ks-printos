# Sample 500 exception format
sample_exception = {
    500: {
        "description": "Internal Server Error",
        "content": {
            "application/json": {
                "example": {
                    "detail": {
                        "message": "Internal Server Error",
                        "log_id": "32c12aed-2178-11ef-ab87-6045bdad83c8",
                    }
                }
            }
        },
    },
}

# Example responses for APIs
response_example_autosuggest = {
    200: {
        "description": "Successful Response",
        "content": {
            "application/json": {
                "example": {
                    "metadata": {
                        "size": 9,
                        "limit": 10,
                        "query": "label",
                        "device": "Indigo 7000",
                        "persona": "operator",
                        "domain": "indigo",
                        "source": "kaas",
                    },
                    "data": [
                        "Blanket reuse label N/A N/A",
                        "DOA Red Label Download this label and attach it to a DOA part for return to HP CA396-06890",
                    ],
                }
            }
        },
    },
}
response_example_autosuggest.update(sample_exception)

# Example responses
response_example_search = {
    200: {
        "description": "Successful Response",
        "content": {
            "application/json": {
                "example": {
                    "metadata": {
                        "size": 1,
                        "limit": 1,
                        "query": "label",
                        "device": "Indigo 7000",
                        "persona": "operator",
                        "domain": "indigo",
                    },
                    "data": [
                        {
                            "documentID": "4AA6-4534EEE",
                            "score": 0.7,
                            "title": "PrintOS Brochure",
                            "description": "End to end brochure, cross business units, describes PrintOS app benefits.",
                            "contentType": "Document",
                            "contentUpdateDate": "2019-07-03T08:35:14Z",
                            "parentDoc": "pdf_8834315_en-US-4.pdf",
                            "products": [
                                "HP Indigo 10000 Digital Press",
                                "HP Indigo 12000 Digital Press",
                            ],
                        },
                    ],
                }
            }
        },
    },
}
response_example_search.update(sample_exception)

# Example responses for kaas
response_examples_extras = {
    200: {
        "description": "Successful Response",
        "content": {
            "application/json": {
                "example": {
                    "documentID": "ish_9230172-9229960-16",
                    "render_link": "https://css.api.hp.com/knowledge/v2/render/6f9MBfc5mjTdAxi2Kb9+QiYuu9Hvi4fIarpLjO3hb3Q_hEJqA_dSTf48NoctmBGAobq52ZCGK3SZtmPHYBNAYa+q9ozEQtOdq9l6Xugo6Cj7of1BG1QLRIg0HG559CAjr7Dm2K6xTdlcMscvXv45DVk5pF6aLHiIPOo1xE88yfB+XnP4lImwlyVoZqZ1VjqtCqC_rhjsghIE_gxFTxaxWhF3mZY+1Hkno66EQm8V4wB0p+eTYgioP_aY4KpKcnPWigGCj2f6eZ6lDarptT784s8mjeewtsMv3XOmK_L_RNbuLhSkHu+pEKddViEgNaX23znzDYtAPfR2ZN2uDhKkxjNzwqbRJ3X2i_dds4WZXH+HtEpFfZreG3A_S4nWCBIYTo8MyOy02ZCYz49XiocoZz8erb_lYo5c33pJOx9HDJ0YxY_MxteHOEgOMQq3PU8mmCFrAdyyody6UKX8RvCBA7SEy+zVQEeqfVkY9a+JXhaYA9zAFreuVC1WS1WMgtoukV4uQgu_T1HQVMT6c4q8aeg1Au1UFJcHVyGH19nbycBIG8ADjlx7WMpxnSmofKpVY86DNDUEaiI8QOCdQubmZ9j+ZxSjdOO_EovDvKgEKsundv7lJ1YRMTXUWqHUfDPXCq14j0yPqD0FDQKGLe4VhgY77T70jAQukHZsdkFGehsuyA4xCYFi3OPaMiOgHaBcR7UIJyOCC1FePBIl7eqfYAe6BHiSRFL6l1lUwg1Ds8jS5kAOzL_nNefBTz7PJIXKvY8eOWm8ZOych4tWiiL8lNku0xXV5gVtEB5YANsCTdNhDE19+EBXIE8TH7rTr6WOt_ZWZ7ak4Mn141QUacY5RkyfteXOw7WbE3neKCg4iPV_oyOKL40UN5obqixZvVDUOpEGsylpTVUiJjwgm+0XpDdr6aAPbgk6TMysaXVWelSu+BqbQBEfhnEsWKn6fe2g8eWUwPi4wRGR579_xXPjII884vZqRF3iaPPS6Hyt4Qx6V6pv8qJ6aHcx5uYOzW8u8s3YbCB6o0jVhcS+Yen95olVyUEVIyRNg1_cNLdmdhBnq+eX85FGBi3biwpnWTUYPrb2alQVICtPU3xk56o5d5H+R5dE3lPT4GpkS8Nf+mAZGclF8i0yeFDSQkhKBzj2Nl3sWsM5rjN9+uUXR833zIw74mE9JcFBksOPti46Rj8hF3NzMdwwuRKV3Sm7qP7qWC353M15J5Ji6ThrozisrpoThSh_2tVNRPwAWm8FgyoWRUmIU1rH5Q6rHQjUzO_3I1clz3HOVDqIdeb4qGJkzJDt8jhAjbNB/ish_9230172-9229960-16",
                }
            }
        },
    },
}
response_examples_extras.update(sample_exception)

# Example response for bulk render URL API


standard_errors = {
    400: {
        "description": "Bad Request",
        "content": {
            "application/json": {
                "example": {
                    "error_code": "E1001",  # Example: Invalid input
                    "message": "Bad Request"
                }
            }
        }
    },
    422: {
        "description": "Validation Error",
        "content": {
            "application/json": {
                "example": {
                    "error_code": "E1002",
                    "message": "Invalid input. Please check your request."
                }
            }
        }
    },
    429: {
        "description": "Rate Limit Exceeded",
        "content": {
            "application/json": {
                "example": {
                    "error_code": "E1003",
                    "message": "Too many requests. Please try again later."
                }
            }
        }
    },
    500: {
        "description": "Internal Server Error",
        "content": {
            "application/json": {
                "example": {
                    "error_code": "E2001",
                    "message": "Unexpected server error. Please contact support."
                }
            }
        }
    },
}

# Example responses
response_example_ai_suggestions = {
    200: {
        "description": "Successful Response",
        "content": {
            "application/json": {
                "example": {
                    "metadata": {
                        "size": 5,
                        "source": ["all"],
                        "query": "million impressions",
                        "device": "HP Indigo WS6000 Digital Press",
                        "persona": "engineer",
                        "domain": "indigo"
                    },
                    "data": {
                        "content": "The term \"million impressions\" in the context of HP Indigo presses typically refers to the preventive maintenance (PM) service that is performed after a certain number of impressions (prints) have been made by the press. Here are some key points...",
                        "question": "million impressions",
                        "citations": "[Document(metadata={'technicalLevel': '', 'disclosureLevel': '287477763180518087286275037723076', 'contentTypeHeader': 'Product Support', 'persona': 'Operator', 'parentDoc': None, 'description': 'HP Indigo WS6000 Digital Press, HP Indigo WS6600 Digital Press, HP Indigo WS6600p Digital Press, HP Indigo WS6800 Digital Press, HP Indigo WS6800p Digital Press, HP Indigo 6900 Digital Press, HP Indigo 6r Digital Press, HP Indigo W7200 Digital Press, HP Indigo W7250 Digital Press, HP Indigo 8000 Digital Press', 'language': 'en', 'store': 'UDPManuals', 'title': '12 Million Impression - Preventive Maintenance for Operator Level 3 — CA493-04670 Rev 01', 'docSource': 'UDP', 'products': ['HP Indigo WS6600p Digital Press', 'HP Indigo WS6800 Digital Press', 'HP Indigo 6r Digital Press']})]"
                    }
                }
            }
        },
    },
}
response_example_ai_suggestions.update(standard_errors)


response_example_search_with_ai_suggestion = {
    200: {
        "description": "Successful Response with Search Results and AI Suggestion",
        "content": {
            "application/json": {
                "example": {
                    "metadata": {
                        "size": 6,
                        "limit": 10,
                        "query": "million impressions",
                        "device": "HP Indigo WS6000 Digital Press",
                        "persona": "engineer",
                        "domain": "indigo"
                    },
                    "search": [
                        {
                            "documentID": "4AA6-4534EEE",
                            "score": 0.7,
                            "title": "PrintOS Brochure",
                            "description": (
                                "End to end brochure, cross business units, describes PrintOS app benefits."
                            ),
                            "contentType": "Document",
                            "contentUpdateDate": "2019-07-03T08:35:14Z",
                            "parentDoc": "pdf_8834315_en-US-4.pdf",
                            "products": [
                                "HP Indigo 10000 Digital Press",
                                "HP Indigo 12000 Digital Press"
                            ],
                        }
                    ],
                    "ai_suggestion": {
                        "content": (
                            "The term \"million impressions\" in the context of HP Indigo presses typically refers to "
                            "the preventive maintenance (PM) service that is performed after a certain number of impressions "
                            "(prints) have been made by the press. Here are some key points..."
                        ),
                        "question": "million impressions",
                        "citations": "[Document(metadata={...})]"
                    }
                }
            }
        },
    }
}

# Append standard error responses
response_example_search_with_ai_suggestion.update(standard_errors)
