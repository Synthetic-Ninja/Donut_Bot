import asyncio
import sys
import time
import re

import selenium.common.exceptions
from loguru import logger
from PyQt6 import uic
from PyQt6.Qt6 import *
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from loguru import logger as logger
import ruamel.yaml

import WebHook
import CustomExceptions
from Moduls import InviteMonitor, EventJoiner, Shazam


class MyLogger:
    def __init__(self, level):
        self.level = level
        logger.remove()
        self.mylog = None

    def console_logger(self, start_message=None):
        #self.mylog = logger.add(sink=GuiUpdaterLogs().show_log, level=self.level)
        self.mylog = logger.add(sink=sys.stderr, level=self.level)
        if start_message is None:
            logger.success(f'Console logger Activated; MODE: "{self.level}"')
        else:
            logger.success(f'{start_message}')

    def webhook_logger(self, start_message=None):
        self.mylog = logger.add(sink=send_log_webhook, level=self.level)
        logger.success(f'Webhook logger Activated; MODE: "{self.level}"')
        # self.mylog = logger.add(sink=GuiUpdaterLogs().show_log, level=self.level)

    def del_logger(self):
        logger.remove(self.mylog)


def send_log_webhook(log):
    color = {'DEBUG': 'grey',
             'SUCCESS': 'green',
             'ERROR': 'red',
             'WARNING': 'orange',
             'INFO': 'blue'}
    log_type = log.split('|')[1].replace(" ", '')
    try:
        hook = WebHook.Webhook(Config().get_config()['webhook_url'])
        hook.send_embed(color=color[log_type], text=log, tittle=log_type)
    except CustomExceptions.WebhookInitializationError:
        GuiUpdaterLogs().show_log("[Webhook error, console display] -- " + log)


class GuiUpdaterLogs:
    def __init__(self):
        self._log_ui = form.textBrowser

    @staticmethod
    def __prepare_log(text):
        styles = {
            'warning': '#ffa500',
            'error': '#ff0000',
            'success': '#a1e330',
            'info': '#FFFFFF',
            'debug': '#039dfc'
        }
        mode = text.split('|')[1].lower().strip()
        return f'<span style=\" color: {styles[mode]};\">{text}</span>'

    def show_log(self, text):
        self._log_ui.append(self.__prepare_log(text=text))


class Config:
    def __init__(self):
        self.yaml = ruamel.yaml.YAML()
        self.yaml.preserve_quotes = True
        self.yaml.explicit_start = True
        with open('./config/config.yaml', encoding='utf8') as stream:  # In windows encoding utf-8
            self.conf = self.yaml.load(stream)

    def get_config(self):
        config = self.conf['SETTINGS']
        return config

    def save_config(self, **args):
        logger.debug(f'Saving config {args}')
        new_config = self.conf['SETTINGS']
        new_config.update(dict(**args))
        with open('./config/config.yaml', 'wb') as stream:  # In windows encoding utf-8
            self.yaml.dump(self.conf, stream)


class Communicate(QObject):
    closeTaskByGui = pyqtSignal()
    closeTaskBySelf = pyqtSignal()
    unlockDeleteButton = pyqtSignal()


class TaskThread(QThread):
    def __init__(self, communicate, module_object, args):
        super().__init__()
        self.communicate = communicate
        self.args = args
        self.module = module_object

    def run(self):
        try:
            self.module = self.module(**self.args, communicator=self.communicate)
            self.module.start_module()
            self.communicate.closeTaskBySelf.emit()
        except RuntimeError as err:
            #KeyboardInterrupt, selenium.common.exceptions.NoSuchWindowException
            logger.error(f'runtime_err {err}')
            self.communicate.closeTaskBySelf.emit()

    def close_all_before_kill(self):
        logger.success('initializing task closing')
        try:
            self.module.stop_module()
        except TypeError:
            logger.warning("Module don't initialize")


class Task:
    def __init__(self, function, **args):
        self.comunicate = Communicate()
        self.thread = TaskThread(self.comunicate, function, args)
        self.item = QListWidgetItem()
        widget = WidgetTask(communicate=self.comunicate, mode=function.__name__, token=args['discord_token'])
        self.item.setSizeHint(QSize(90, 50))
        form.listWidget.addItem(self.item)
        form.listWidget.setItemWidget(self.item, widget)
        threads.append(self.thread)
        self.comunicate.closeTaskByGui.connect(lambda: self.delete_task(text='Task removed by User'))
        self.comunicate.closeTaskBySelf.connect(lambda: self.delete_task(text='Task removed by Self'))
        self.comunicate.unlockDeleteButton.connect(lambda: widget.enable_button())
        self.thread.start()

    def delete_task(self, text):
        form.listWidget.takeItem(form.listWidget.row(self.item))
        self.thread.close_all_before_kill()
        self.thread.terminate()
        threads.remove(self.thread)
        logger.success(text)


class WidgetTask(QWidget):
    def __init__(self, communicate, mode, token):
        super().__init__()
        self.setObjectName('mywidget')
        self.widget = QWidget(self)
        self.widget.resize(600, 40)
        self.widget.setObjectName('maintask')
        layout = QGridLayout(self.widget)
        task_mode = QLabel(f'Mode: {mode}')
        task_mode.setObjectName('task_mode_label')
        task_token = QLabel(f'Token: {token}')
        task_token.setObjectName('task_token_label')
        self.btn = QPushButton('Delete task')
        self.btn.setVisible(False)
        self.btn.setEnabled(False)
        self.btn.clicked.connect(lambda: communicate.closeTaskByGui.emit())
        self.btn.setObjectName('close_task_btn')
        layout.addWidget(task_mode, 0, 1)
        layout.addWidget(task_token, 0, 2)
        layout.addWidget(self.btn, 0, 3)
        self.setStyleSheet('''
         #maintask {
                    background-color: rgb(34, 36, 46);
                    border: 1px solid;
                    border-radius: 10px;
                    }

        #close_task_btn{
                    background-color: rgb(34, 36, 46);
                    border: 0.5px solid rgb(255, 80, 104);
                    border-radius: 5px;

                    }
        #close_task_btn::hover{
                    background-color: rgb(34, 36, 46);
                    border: 0.5px solid rgb(255, 80, 104);
                    color :  white;
                    }
        
        #task_mode_label{
                        background-color: rgb(34, 36, 46);
                            }
        #task_token_label{
                        background-color: rgb(34, 36, 46);
                            }

                            ''')

    def enable_button(self):
        self.btn.setEnabled(True)
        self.btn.setVisible(True)


def show_page(page: str):
    pages = {'settings_page': form.settings_page,
             'loger_page': form.loger_page,
             'invite_manager_page': form.invite_manager_page,
             'spam_bot_page': form.spam_bot_page,
             'giveaway_bot_page': form.giveaway_bot_page,
             'home_page': form.home_page}

    if page in pages:
        form.stackedWidget.setCurrentWidget(pages[page])
        logger.debug(f'Window switch to {page}')


def start_invite_manager():
    _config = Config().get_config()
    discord_token = form.edit_discord_token.text()
    api_twitter_key = form.edit_api.text()
    api_twitter_secret = form.edit_api_secret.text()
    twitter_acess_token = form.edit_acess_token.text()
    twitter_acess_secret = form.edit_acess_token_secret.text()
    monitor_users = form.edit_accounts_filter.text().split(';')
    Task(InviteMonitor,
         discord_token=discord_token,
         twitter_api=api_twitter_key,
         twitter_api_secret=api_twitter_secret,
         twitter_access=twitter_acess_token,
         twitter_access_secret=twitter_acess_secret,
         monitoring_users=monitor_users)


def start_giveaway_bot():
    discord_token = form.edit_discord_token_giveawaybot.text()
    channel = int(form.edit_giveaway_channel.text())
    author_id = int(form.edit_giveway_bot_id.text())
    embed = form.embed_mode_checkbox.checkState()
    keyword = form.edit_giveaway_keywords.text()
    reaction_emoji = form.edit_reaction_emoji.text()
    loop = asyncio.new_event_loop()
    Task(Shazam,
         discord_token=discord_token,
         channel=channel,
         author_id=author_id,
         embed=embed,
         keyword=keyword,
         reaction_emoji=reaction_emoji,
         loop=loop
         )


def start_spam_bot():
    pass


def load_settings_in_gui():
    config = Config().get_config()
    form.edit_path_to_webdriver.setText(config['path_to_webdriver'])
    form.headless_checkbox.setChecked(config['headless_webdriver'])
    form.webhook_checkbox.setChecked(config['webhook_logger'])
    form.edit_webhook.setText(config['webhook_url'])
    form.debug_mode_checkbox.setChecked(config['debug_mode'])


def save_settings():
    Config().save_config(
        #path_to_webdriver=form.edit_path_to_webdriver.text(),
        #headless_webdriver=form.headless_checkbox.isChecked(),
        webhook_logger=form.webhook_checkbox.isChecked(),
        webhook_url=form.edit_webhook.text(),
        debug_mode=form.debug_mode_checkbox.isChecked())


def printer(start_text, stoptext):
    logger.info(start_text)
    time.sleep(3)
    logger.success(stoptext)


def test():
    a = Config().get_config()
    print(a['headless_webdriver'])


def kill_all_threads():
    if threads:
        for active_thread in threads:
            active_thread.close_all_before_kill()
            active_thread.terminate()


if __name__ == '__main__':
    # Version
    app_version = 'alpha_v0.0.1'
    # Interpretation ui to python file
    Form, Window = uic.loadUiType("Donut_gui.ui")
    app = QApplication([])
    window = Window()
    form = Form()
    form.setupUi(window)

    # Initializing logger
    mylogger = MyLogger('INFO' if Config().get_config()['debug_mode'] is False else 'DEBUG')
    app_config = Config()
    if app_config.get_config()['webhook_logger'] is True and app_config.get_config()['webhook_url'] != '':
        mylogger.webhook_logger()
    else:
        mylogger.console_logger()
    window.show()
    window.setWindowTitle("DonutBot_" + app_version)
    form.version_label.setText(f'App Version: {app_version}')
    load_settings_in_gui()
    threads = []
    tasks = []

    #####BLOCKING BROKEN MODULE##########
    # Giveaway module
    form.giveaway_bot_button.setVisible(False)
    form.giveaway_bot_button.setEnabled(False)
    # Spambot module
    form.spambot_button.setVisible(False)
    form.spambot_button.setEnabled(False)
    # Settings for webdriver
    form.path_to_webdriver_label.setVisible(False)
    form.edit_path_to_webdriver.setVisible(False)
    form.headless_checkbox.setVisible(False)



    # home button click handling
    form.home_button.clicked.connect(lambda: show_page('home_page'))

    # invite_manager_button click handling
    form.invite_manager_button.clicked.connect(lambda: show_page('invite_manager_page'))

    # giveaway_bot_button click handling
    form.giveaway_bot_button.clicked.connect(lambda: show_page('giveaway_bot_page'))

    # spambot button click handling
    form.spambot_button.clicked.connect(lambda: show_page('spam_bot_page'))

    # logger button click handling
    form.logger_button.clicked.connect(lambda: show_page('loger_page'))

    # settings button click handling
    form.settings_button.clicked.connect(lambda: show_page('settings_page'))

    # logout button click handling
    form.logout_button.clicked.connect(lambda: sys.exit(kill_all_threads()))

    # save settings button handling
    form.save_settings_button.clicked.connect(lambda: save_settings())

    # start invite manager button handler
    form.start_invite_manager.clicked.connect(lambda: start_invite_manager())

    # start giveaway button handler
    form.start_giveawaybot.clicked.connect(lambda: start_giveaway_bot())

    del app_config
    try:
        sys.exit(app.exec())
    except SystemExit:
        sys.exit(kill_all_threads())

