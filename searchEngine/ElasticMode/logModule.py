# -*- coding:utf-8 -*-
# @Author : tzy

import logging

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%m/%d/%Y %H:%M:%S',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


def INFO(msg):
    logger.info(msg)

def DEBUG(msg):
    logger.debug(msg)

def WARNING(msg):
    logger.warning(msg)

def ERROR(msg):
    logger.error(msg)