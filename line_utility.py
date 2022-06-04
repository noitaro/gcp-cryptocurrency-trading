import aiohttp


class line_utility:

    _channel_access_token = None

    def __init__(self, setting) -> None:
        self._channel_access_token = setting['channel_access_token']
        pass

    def get_order_messages(self, title: str, order_text: list):
        contents = []
        for order in order_text:
            contents.append({
                "type": "box",
                "layout": "baseline",
                "spacing": "sm",
                "contents": [
                    {
                        "type": "text",
                        "text": order['title'],
                        "color": "#aaaaaa",
                        "size": "sm",
                        "flex": 3
                    },
                    {
                        "type": "text",
                        "text": str(order['text']),
                        "wrap": True,
                        "color": "#666666",
                        "size": "sm",
                        "flex": 5
                    }
                ]
            })
            pass

        messages = {
            "type": "flex",
            "altText": "This is a Flex Message",
            "contents": {
                "type": "bubble",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": title,
                            "weight": "bold",
                            "size": "md",
                            "adjustMode": "shrink-to-fit"
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "margin": "lg",
                            "spacing": "sm",
                            "contents": contents
                        }
                    ]
                }
            }
        }
        return messages

    def get_trigger_messages(self, is_deadcross, is_cci_trigger, vwma1, vwma2, cci_old1, cci_old2, CCI_LOWERBAND):
        messages = {
            "type": "flex",
            "altText": "This is a Flex Message",
            "contents": {
                "type": "bubble",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": f"トリガー判定:{is_deadcross and is_cci_trigger}",
                            "weight": "bold",
                            "size": "md"
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "margin": "lg",
                            "spacing": "sm",
                            "contents": [
                                {
                                    "type": "box",
                                    "layout": "baseline",
                                    "spacing": "sm",
                                    "contents": [
                                        {
                                            "type": "text",
                                            "text": f"VWMA:{is_deadcross}",
                                            "color": "#aaaaaa",
                                            "size": "sm",
                                            "flex": 3
                                        },
                                        {
                                            "type": "text",
                                            "text": f"{vwma1}<{vwma2}",
                                            "color": "#666666",
                                            "size": "sm",
                                            "flex": 5
                                        }
                                    ]
                                },
                                {
                                    "type": "box",
                                    "layout": "baseline",
                                    "spacing": "sm",
                                    "contents": [
                                        {
                                            "type": "text",
                                            "text": f"CCI:{is_cci_trigger}",
                                            "color": "#aaaaaa",
                                            "size": "sm",
                                            "flex": 3
                                        },
                                        {
                                            "type": "text",
                                            "text": f"{cci_old1}<{CCI_LOWERBAND}<{cci_old2}",
                                            "color": "#666666",
                                            "size": "sm",
                                            "flex": 5
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            }
        }
        return messages

    def get_kessai_messages(self, is_cci_kessai, cci_old1, cci_old2, CCI_UPPERBAND):
        messages = {
            "type": "flex",
            "altText": "This is a Flex Message",
            "contents": {
                "type": "bubble",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": f"決済判定:{is_cci_kessai}",
                            "weight": "bold",
                            "size": "md"
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "margin": "lg",
                            "spacing": "sm",
                            "contents": [
                                {
                                    "type": "box",
                                    "layout": "baseline",
                                    "spacing": "sm",
                                    "contents": [
                                        {
                                            "type": "text",
                                            "text": f"CCI:{is_cci_kessai}",
                                            "color": "#aaaaaa",
                                            "size": "sm",
                                            "flex": 3
                                        },
                                        {
                                            "type": "text",
                                            "text": f"{cci_old2}<={CCI_UPPERBAND}<{cci_old1}",
                                            "color": "#666666",
                                            "size": "sm",
                                            "flex": 5
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            }
        }
        return messages

    async def broadcast_send(self, messages: str, notification_disabled: bool = False):

        async with aiohttp.ClientSession() as session:
            session.headers.add('Content-Type', 'application/json')
            session.headers.add('Authorization', f'Bearer {self._channel_access_token}')

            url = 'https://api.line.me/v2/bot/message/broadcast'
            data = {'messages': [messages], 'notificationDisabled': notification_disabled}
            print(data)
            async with session.post(url, json=data) as response:
                print(response.status)
                print(await response.text())
                pass
            pass
        pass

    def get_messages_text(self, text: str):
        messages = {
            "type": "text",
            "text": text
        }
        return messages

    def get_messages_ok_cancel(self, title_text: str, message: str, ok: dict, cancel: dict):
        contents = []
        contents.append({
            "type": "text",
            "text": title_text,
            "weight": "bold",
            "size": "md",
            "adjustMode": "shrink-to-fit"
        })
        if message != "":
            contents.append({
                "type": "text",
                "text": message,
                "wrap": True,
                "size": "sm"
            })
            pass

        messages = {
            "type": "flex",
            "altText": "This is a Flex Message",
            "contents": {
                "type": "bubble",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": contents
                },
                "footer": self.get_footer(ok, cancel)
            }
        }
        return messages

    def get_footer(self, ok: dict, cancel: dict):
        footer = {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "flex": 0,
            "contents": [
                {
                    "type": "button",
                    "style": "primary",
                    "height": "sm",
                    "action": {
                        "type": "message",
                        "label": ok['label'],
                        "text": ok['text']
                    }
                },
                {
                    "type": "button",
                    "style": "secondary",
                    "height": "sm",
                    "action": {
                        "type": "message",
                        "label": cancel['label'],
                        "text": cancel['text']
                    }
                }
            ]
        }
        return footer

    def get_change_api_check(self, title_text: str, change_text: list, ok: dict, cancel: dict):
        contents = []
        for change in change_text:
            contents.append({
                "type": "box",
                "layout": "baseline",
                "spacing": "sm",
                "contents": [
                    {
                        "type": "text",
                        "text": change["title"],
                        "color": "#aaaaaa",
                        "size": "sm",
                        "flex": 3
                    },
                    {
                        "type": "text",
                        "text": change["text"],
                        "wrap": True,
                        "color": "#666666",
                        "size": "sm",
                        "flex": 5
                    }
                ]
            })
            pass

        messages = {
            "type": "flex",
            "altText": "This is a Flex Message",
            "contents": {
                "type": "bubble",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": title_text,
                            "weight": "bold",
                            "size": "md",
                            "adjustMode": "shrink-to-fit"
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "margin": "lg",
                            "spacing": "sm",
                            "contents": contents
                        }
                    ]
                },
                "footer": self.get_footer(ok, cancel)
            }
        }
        return messages

    def get_menu(self, title_text: str, menu_text: list):
        contents = []
        for menu in menu_text:
            contents.append({
                "type": "button",
                "style": menu['style'],
                "height": "sm",
                "action": {
                    "type": "message",
                    "label": menu['label'],
                    "text": menu['text']
                }
            })
            pass

        messages = {
            "type": "flex",
            "altText": "This is a Flex Message",
            "contents": {
                "type": "bubble",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": title_text,
                            "weight": "bold",
                            "size": "md",
                            "adjustMode": "shrink-to-fit"
                        }
                    ]
                },
                "footer": {
                    "type": "box",
                    "layout": "vertical",
                    "spacing": "sm",
                    "flex": 0,
                    "contents": contents
                }
            }
        }
        return messages

    def get_operating_status(self, title_text: str, exchange_text: list):
        contents = []
        for exchange in exchange_text:
            contents.append({
                "type": "box",
                "layout": "baseline",
                "spacing": "sm",
                "contents": [
                    {
                        "type": "text",
                        "text": exchange['text1'],
                        "color": "#aaaaaa",
                        "size": "sm",
                        "flex": 2
                    },
                    {
                        "type": "text",
                        "text": exchange['text2'],
                        "wrap": True,
                        "color": "#666666",
                        "size": "sm",
                        "flex": 5
                    }
                ]
            })
            pass

        messages = {
            "type": "flex",
            "altText": "This is a Flex Message",
            "contents": {
                "type": "bubble",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": title_text,
                            "weight": "bold",
                            "size": "md",
                            "adjustMode": "shrink-to-fit"
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "margin": "lg",
                            "spacing": "sm",
                            "contents": contents
                        }
                    ]
                }
            }
        }
        return messages

    def get_other(self, menu_text: list, other_menu: list = []):
        contents = []
        for text in menu_text:
            contents.append({
                "type": "button",
                "style": "primary",
                "height": "sm",
                "action": {
                    "type": "message",
                    "label": text,
                    "text": text
                }
            })
            pass

        for text in other_menu:
            contents.append({
                "type": "button",
                "style": "secondary",
                "height": "sm",
                "action": {
                    "type": "message",
                    "label": text,
                    "text": text
                }
            })
            pass

        messages = {
            "type": "flex",
            "altText": "This is a Flex Message",
            "contents": {
                "type": "bubble",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "LINEから出来ること",
                            "weight": "bold",
                            "size": "md",
                            "adjustMode": "shrink-to-fit"
                        }
                    ]
                },
                "footer": {
                    "type": "box",
                    "layout": "vertical",
                    "spacing": "sm",
                    "flex": 0,
                    "contents": contents
                }
            }
        }
        return messages

    def get_url(self, url: str):
        messages = {
            "type": "flex",
            "altText": "This is a Flex Message",
            "contents": {
                "type": "bubble",
                "footer": {
                    "type": "box",
                    "layout": "vertical",
                    "spacing": "sm",
                    "contents": [
                        {
                            "type": "button",
                            "style": "link",
                            "height": "sm",
                            "action": {
                                "type": "uri",
                                "label": "ブラウザで開く",
                                "uri": url
                            }
                        }
                    ],
                    "flex": 0
                }
            }
        }
        return messages

    pass
