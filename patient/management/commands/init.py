import json
import os
import logging

from django.core.management.base import BaseCommand
from patient.models import RelationshipTable  # Replace 'your_app' with your actual app name

# 绝对路径
from django.conf import settings

BASE_DIR = settings.BASE_DIR


class Command(BaseCommand):
    help = 'Initialize RelationshipTable with JSON data'

    def handle(self, *args, **options):

        # file_path = os.path.join(settings.BASE_DIR, 'a_first_map.txt')
        # with open(file_path, 'r') as file:
        #     # print(file)
        #     a_first_map = json.load(file)
        #     # print(a_first_map)
        #
        # file_path = os.path.join(settings.BASE_DIR, 'a_second_map.txt')
        # with open(file_path, 'r') as file:
        #     a_second_map = json.load(file)
        #     print(a_second_map)
        #
        # file_path = os.path.join(settings.BASE_DIR, 'pro_first_map.txt')
        # with open(file_path, 'r') as file:
        #     pro_first_map = json.load(file)
        #
        # file_path = os.path.join(settings.BASE_DIR, 'pro_second_map.txt')
        # with open(file_path, 'r') as file:
        #     pro_second_map = json.load(file)
        #
        # file_path = os.path.join(settings.BASE_DIR, 's_first_map.txt')
        # with open(file_path, 'r') as file:
        #     s_first_map = json.load(file)
        a_first_map = [
  {"base_arc_curvature_radius": 7.5, "lens_type_number": 0.23, "lens_type": "A", "belongs_level": 1},
  {"base_arc_curvature_radius": 7.54, "lens_type_number": 0.23, "lens_type": "A", "belongs_level": 1},
  {"base_arc_curvature_radius": 7.58, "lens_type_number": 0.23, "lens_type": "A", "belongs_level": 1},
  {"base_arc_curvature_radius": 7.63, "lens_type_number": 0.23, "lens_type": "A", "belongs_level": 1},
  {"base_arc_curvature_radius": 7.67, "lens_type_number": 0.23, "lens_type": "A", "belongs_level": 1},
  {"base_arc_curvature_radius": 7.71, "lens_type_number": 0.23, "lens_type": "A", "belongs_level": 1},
  {"base_arc_curvature_radius": 7.76, "lens_type_number": 0.23, "lens_type": "A", "belongs_level": 1},
  {"base_arc_curvature_radius": 7.8, "lens_type_number": 0.23, "lens_type": "A", "belongs_level": 1},
  {"base_arc_curvature_radius": 7.85, "lens_type_number": 0.23, "lens_type": "A", "belongs_level": 1},
  {"base_arc_curvature_radius": 7.9, "lens_type_number": 0.23, "lens_type": "A", "belongs_level": 1},
  {"base_arc_curvature_radius": 7.94, "lens_type_number": 0.23, "lens_type": "A", "belongs_level": 1},
  {"base_arc_curvature_radius": 7.99, "lens_type_number": 0.23, "lens_type": "A", "belongs_level": 1},
  {"base_arc_curvature_radius": 8.04, "lens_type_number": 0.23, "lens_type": "A", "belongs_level": 1},
  {"base_arc_curvature_radius": 8.08, "lens_type_number": 0.23, "lens_type": "A", "belongs_level": 1},
  {"base_arc_curvature_radius": 8.13, "lens_type_number": 0.23, "lens_type": "A", "belongs_level": 1},
  {"base_arc_curvature_radius": 8.18, "lens_type_number": 0.23, "lens_type": "A", "belongs_level": 1},
  {"base_arc_curvature_radius": 8.23, "lens_type_number": 0.23, "lens_type": "A", "belongs_level": 1},
  {"base_arc_curvature_radius": 8.28, "lens_type_number": 0.23, "lens_type": "A", "belongs_level": 1},
  {"base_arc_curvature_radius": 8.33, "lens_type_number": 0.23, "lens_type": "A", "belongs_level": 1},
  {"base_arc_curvature_radius": 8.39, "lens_type_number": 0.23, "lens_type": "A", "belongs_level": 1},
  {"base_arc_curvature_radius": 8.44, "lens_type_number": 0.23, "lens_type": "A", "belongs_level": 1},
  {"base_arc_curvature_radius": 8.49, "lens_type_number": 0.23, "lens_type": "A", "belongs_level": 1},
  {"base_arc_curvature_radius": 8.54, "lens_type_number": 0.23, "lens_type": "A", "belongs_level": 1},
  {"base_arc_curvature_radius": 8.6, "lens_type_number": 0.23, "lens_type": "A", "belongs_level": 1},
  {"base_arc_curvature_radius": 8.65, "lens_type_number": 0.23, "lens_type": "A", "belongs_level": 1},
  {"base_arc_curvature_radius": 8.71, "lens_type_number": 0.23, "lens_type": "A", "belongs_level": 1},
  {"base_arc_curvature_radius": 8.77, "lens_type_number": 0.23, "lens_type": "A", "belongs_level": 1},
  {"base_arc_curvature_radius": 8.82, "lens_type_number": 0.23, "lens_type": "A", "belongs_level": 1},
  {"base_arc_curvature_radius": 8.88, "lens_type_number": 0.23, "lens_type": "A", "belongs_level": 1},
  {"base_arc_curvature_radius": 8.94, "lens_type_number": 0.23, "lens_type": "A", "belongs_level": 1},
  {"base_arc_curvature_radius": 9, "lens_type_number": 0.23, "lens_type": "A", "belongs_level": 1},
  {"base_arc_curvature_radius": 9.06, "lens_type_number": 0.23, "lens_type": "A", "belongs_level": 1},
  {"base_arc_curvature_radius": 9.12, "lens_type_number": 0.23, "lens_type": "A", "belongs_level": 1},
  {"base_arc_curvature_radius": 9.18, "lens_type_number": 0.23, "lens_type": "A", "belongs_level": 1},
  {"base_arc_curvature_radius": 9.25, "lens_type_number": 0.23, "lens_type": "A", "belongs_level": 1},
  {"base_arc_curvature_radius": 9.31, "lens_type_number": 0.23, "lens_type": "A", "belongs_level": 1},
  {"base_arc_curvature_radius": 9.38, "lens_type_number": 0.23, "lens_type": "A", "belongs_level": 1},
  {"base_arc_curvature_radius": 9.44, "lens_type_number": 0.23, "lens_type": "A", "belongs_level": 1},
  {"base_arc_curvature_radius": 9.51, "lens_type_number": 0.23, "lens_type": "A", "belongs_level": 1},
  {"base_arc_curvature_radius": 9.57, "lens_type_number": 0.23, "lens_type": "A", "belongs_level": 1},
  {"base_arc_curvature_radius": 9.64, "lens_type_number": 0.23, "lens_type": "A", "belongs_level": 1},
  {"base_arc_curvature_radius": 9.71, "lens_type_number": 0.23, "lens_type": "A", "belongs_level": 1},
  {"base_arc_curvature_radius": 9.78, "lens_type_number": 0.23, "lens_type": "A", "belongs_level": 1},
  {"base_arc_curvature_radius": 9.85, "lens_type_number": 0.23, "lens_type": "A", "belongs_level": 1},
  {"base_arc_curvature_radius": 9.93, "lens_type_number": 0.23, "lens_type": "A", "belongs_level": 1},
  {"base_arc_curvature_radius": 10, "lens_type_number": 0.23, "lens_type": "A", "belongs_level": 1},
  {"base_arc_curvature_radius": 10.08, "lens_type_number": 0.23, "lens_type": "A", "belongs_level": 1},
  {"base_arc_curvature_radius": 10.15, "lens_type_number": 0.23, "lens_type": "A", "belongs_level": 1},
  {"base_arc_curvature_radius": 10.23, "lens_type_number": 0.23, "lens_type": "A", "belongs_level": 1},
  {"base_arc_curvature_radius": 10.31, "lens_type_number": 0.23, "lens_type": "A", "belongs_level": 1},
  {"base_arc_curvature_radius": 10.39, "lens_type_number": 0.23, "lens_type": "A", "belongs_level": 1},
  {"base_arc_curvature_radius": 10.47, "lens_type_number": 0.23, "lens_type": "A", "belongs_level": 1},
  {"base_arc_curvature_radius": 10.55, "lens_type_number": 0.23, "lens_type": "A", "belongs_level": 1},
  {"base_arc_curvature_radius": 10.63, "lens_type_number": 0.23, "lens_type": "A", "belongs_level": 1},
  {"base_arc_curvature_radius": 10.71, "lens_type_number": 0.23, "lens_type": "A", "belongs_level": 1}
]
        a_second_map = [
    {
        "base_arc_curvature_radius": 7.024,
        "lens_type_number": -1.5,
        "lens_type": "A",
        "belongs_level": 2
    },
    {
        "base_arc_curvature_radius": 7.066226,
        "lens_type_number": -1.5,
        "lens_type": "A",
        "belongs_level": 2
    },
    {
        "base_arc_curvature_radius": 7.108702,
        "lens_type_number": -1.5,
        "lens_type": "A",
        "belongs_level": 2
    },
    {
        "base_arc_curvature_radius": 7.161797,
        "lens_type_number": -1.5,
        "lens_type": "A",
        "belongs_level": 2
    },
    {
        "base_arc_curvature_radius": 7.204273,
        "lens_type_number": -1.5,
        "lens_type": "A",
        "belongs_level": 2
    },
    {
        "base_arc_curvature_radius": 7.246749,
        "lens_type_number": -1.5,
        "lens_type": "A",
        "belongs_level": 2
    },
    {
        "base_arc_curvature_radius": 7.3,
        "lens_type_number": -1.5,
        "lens_type": "A",
        "belongs_level": 2
    },
    {
        "base_arc_curvature_radius": 7.34232,
        "lens_type_number": -1.5,
        "lens_type": "A",
        "belongs_level": 2
    },
    {
        "base_arc_curvature_radius": 7.395415,
        "lens_type_number": -1.5,
        "lens_type": "A",
        "belongs_level": 2
    },
    {
        "base_arc_curvature_radius": 7.44851,
        "lens_type_number": -1.5,
        "lens_type": "A",
        "belongs_level": 2
    },
    {
        "base_arc_curvature_radius": 7.490986,
        "lens_type_number": -1.5,
        "lens_type": "A",
        "belongs_level": 2
    },
    {
        "base_arc_curvature_radius": 7.544081,
        "lens_type_number": -1.5,
        "lens_type": "A",
        "belongs_level": 2
    },
    {
        "base_arc_curvature_radius": 7.597176,
        "lens_type_number": -1.5,
        "lens_type": "A",
        "belongs_level": 2
    },
    {
        "base_arc_curvature_radius": 7.639652,
        "lens_type_number": -1.5,
        "lens_type": "A",
        "belongs_level": 2
    },
    {
        "base_arc_curvature_radius": 7.693,
        "lens_type_number": -1.5,
        "lens_type": "A",
        "belongs_level": 2
    },
    {
        "base_arc_curvature_radius": 7.642,
        "lens_type_number": -1.9,
        "lens_type": "A",
        "belongs_level": 2
    },
    {
        "base_arc_curvature_radius": 7.695512,
        "lens_type_number": -1.9,
        "lens_type": "A",
        "belongs_level": 2
    },
    {
        "base_arc_curvature_radius": 7.748732,
        "lens_type_number": -1.9,
        "lens_type": "A",
        "belongs_level": 2
    },
    {
        "base_arc_curvature_radius": 7.801952,
        "lens_type_number": -1.9,
        "lens_type": "A",
        "belongs_level": 2
    },
    {
        "base_arc_curvature_radius": 7.865816,
        "lens_type_number": -1.9,
        "lens_type": "A",
        "belongs_level": 2
    },
    {
        "base_arc_curvature_radius": 7.919,
        "lens_type_number": -1.9,
        "lens_type": "A",
        "belongs_level": 2
    },
    {
        "base_arc_curvature_radius": 7.972256,
        "lens_type_number": -1.9,
        "lens_type": "A",
        "belongs_level": 2
    },
    {
        "base_arc_curvature_radius": 8.025476,
        "lens_type_number": -1.9,
        "lens_type": "A",
        "belongs_level": 2
    },
    {
        "base_arc_curvature_radius": 8.08934,
        "lens_type_number": -1.9,
        "lens_type": "A",
        "belongs_level": 2
    },
    {
        "base_arc_curvature_radius": 8.14256,
        "lens_type_number": -1.9,
        "lens_type": "A",
        "belongs_level": 2
    },
    {
        "base_arc_curvature_radius": 8.206424,
        "lens_type_number": -1.9,
        "lens_type": "A",
        "belongs_level": 2
    },
    {
        "base_arc_curvature_radius": 8.27,
        "lens_type_number": -1.9,
        "lens_type": "A",
        "belongs_level": 2
    },
    {
        "base_arc_curvature_radius": 8.226,
        "lens_type_number": -2.3,
        "lens_type": "A",
        "belongs_level": 2
    },
    {
        "base_arc_curvature_radius": 8.29002,
        "lens_type_number": -2.3,
        "lens_type": "A",
        "belongs_level": 2
    },
    {
        "base_arc_curvature_radius": 8.35401,
        "lens_type_number": -2.3,
        "lens_type": "A",
        "belongs_level": 2
    },
    {
        "base_arc_curvature_radius": 8.418,
        "lens_type_number": -2.3,
        "lens_type": "A",
        "belongs_level": 2
    },
    {
        "base_arc_curvature_radius": 8.48199,
        "lens_type_number": -2.3,
        "lens_type": "A",
        "belongs_level": 2
    },
    {
        "base_arc_curvature_radius": 8.547,
        "lens_type_number": -2.3,
        "lens_type": "A",
        "belongs_level": 2
    },
    {
        "base_arc_curvature_radius": 8.60997,
        "lens_type_number": -2.3,
        "lens_type": "A",
        "belongs_level": 2
    },
    {
        "base_arc_curvature_radius": 8.684625,
        "lens_type_number": -2.3,
        "lens_type": "A",
        "belongs_level": 2
    },
    {
        "base_arc_curvature_radius": 8.748615,
        "lens_type_number": -2.3,
        "lens_type": "A",
        "belongs_level": 2
    },
    {
        "base_arc_curvature_radius": 8.82327,
        "lens_type_number": -2.3,
        "lens_type": "A",
        "belongs_level": 2
    },
    {
        "base_arc_curvature_radius": 8.88726,
        "lens_type_number": -2.3,
        "lens_type": "A",
        "belongs_level": 2
    },
    {
        "base_arc_curvature_radius": 8.962,
        "lens_type_number": -2.3,
        "lens_type": "A",
        "belongs_level": 2
    },
    {
        "base_arc_curvature_radius": 8.892,
        "lens_type_number": -2.9,
        "lens_type": "A",
        "belongs_level": 2
    },
    {
        "base_arc_curvature_radius": 8.967736,
        "lens_type_number": -2.9,
        "lens_type": "A",
        "belongs_level": 2
    },
    {
        "base_arc_curvature_radius": 9.042454,
        "lens_type_number": -2.9,
        "lens_type": "A",
        "belongs_level": 2
    },
    {
        "base_arc_curvature_radius": 9.117172,
        "lens_type_number": -2.9,
        "lens_type": "A",
        "belongs_level": 2
    },
    {
        "base_arc_curvature_radius": 9.19189,
        "lens_type_number": -2.9,
        "lens_type": "A",
        "belongs_level": 2
    },
    {
        "base_arc_curvature_radius": 9.277282,
        "lens_type_number": -2.9,
        "lens_type": "A",
        "belongs_level": 2
    },
    {
        "base_arc_curvature_radius": 9.352,
        "lens_type_number": -2.9,
        "lens_type": "A",
        "belongs_level": 2
    },
    {
        "base_arc_curvature_radius": 9.439,
        "lens_type_number": -2.9,
        "lens_type": "A",
        "belongs_level": 2
    },
    {
        "base_arc_curvature_radius": 9.51211,
        "lens_type_number": -2.9,
        "lens_type": "A",
        "belongs_level": 2
    },
    {
        "base_arc_curvature_radius": 9.597502,
        "lens_type_number": -2.9,
        "lens_type": "A",
        "belongs_level": 2
    },
    {
        "base_arc_curvature_radius": 9.682894,
        "lens_type_number": -2.9,
        "lens_type": "A",
        "belongs_level": 2
    },
    {
        "base_arc_curvature_radius": 9.768286,
        "lens_type_number": -2.9,
        "lens_type": "A",
        "belongs_level": 2
    },
    {
        "base_arc_curvature_radius": 9.853678,
        "lens_type_number": -2.9,
        "lens_type": "A",
        "belongs_level": 2
    },
    {
        "base_arc_curvature_radius": 9.93907,
        "lens_type_number": -2.9,
        "lens_type": "A",
        "belongs_level": 2
    },
    {
        "base_arc_curvature_radius": 10.024462,
        "lens_type_number": -2.9,
        "lens_type": "A",
        "belongs_level": 2
    },
    {
        "base_arc_curvature_radius": 10.109,
        "lens_type_number": -2.9,
        "lens_type": "A",
        "belongs_level": 2
    }
]
        pro_first_map = [
  {"base_arc_curvature_radius": 7.5, "lens_type_number": 0.23, "lens_type": "PRO", "belongs_level": 1},
  {"base_arc_curvature_radius": 7.54, "lens_type_number": 0.23, "lens_type": "PRO", "belongs_level": 1},
  {"base_arc_curvature_radius": 7.58, "lens_type_number": 0.23, "lens_type": "PRO", "belongs_level": 1},
  {"base_arc_curvature_radius": 7.63, "lens_type_number": 0.23, "lens_type": "PRO", "belongs_level": 1},
  {"base_arc_curvature_radius": 7.67, "lens_type_number": 0.23, "lens_type": "PRO", "belongs_level": 1},
  {"base_arc_curvature_radius": 7.71, "lens_type_number": 0.23, "lens_type": "PRO", "belongs_level": 1},
  {"base_arc_curvature_radius": 7.76, "lens_type_number": 0.23, "lens_type": "PRO", "belongs_level": 1},
  {"base_arc_curvature_radius": 7.8, "lens_type_number": 0.23, "lens_type": "PRO", "belongs_level": 1},
  {"base_arc_curvature_radius": 7.85, "lens_type_number": 0.23, "lens_type": "PRO", "belongs_level": 1},
  {"base_arc_curvature_radius": 7.9, "lens_type_number": 0.23, "lens_type": "PRO", "belongs_level": 1},
  {"base_arc_curvature_radius": 7.94, "lens_type_number": 0.23, "lens_type": "PRO", "belongs_level": 1},
  {"base_arc_curvature_radius": 7.99, "lens_type_number": 0.23, "lens_type": "PRO", "belongs_level": 1},
  {"base_arc_curvature_radius": 8.04, "lens_type_number": 0.23, "lens_type": "PRO", "belongs_level": 1},
  {"base_arc_curvature_radius": 8.08, "lens_type_number": 0.23, "lens_type": "PRO", "belongs_level": 1},
  {"base_arc_curvature_radius": 8.13, "lens_type_number": 0.23, "lens_type": "PRO", "belongs_level": 1},
  {"base_arc_curvature_radius": 8.18, "lens_type_number": 0.23, "lens_type": "PRO", "belongs_level": 1},
  {"base_arc_curvature_radius": 8.23, "lens_type_number": 0.23, "lens_type": "PRO", "belongs_level": 1},
  {"base_arc_curvature_radius": 8.28, "lens_type_number": 0.23, "lens_type": "PRO", "belongs_level": 1},
  {"base_arc_curvature_radius": 8.33, "lens_type_number": 0.23, "lens_type": "PRO", "belongs_level": 1},
  {"base_arc_curvature_radius": 8.39, "lens_type_number": 0.23, "lens_type": "PRO", "belongs_level": 1},
  {"base_arc_curvature_radius": 8.44, "lens_type_number": 0.23, "lens_type": "PRO", "belongs_level": 1},
  {"base_arc_curvature_radius": 8.49, "lens_type_number": 0.23, "lens_type": "PRO", "belongs_level": 1},
  {"base_arc_curvature_radius": 8.54, "lens_type_number": 0.23, "lens_type": "PRO", "belongs_level": 1},
  {"base_arc_curvature_radius": 8.6, "lens_type_number": 0.23, "lens_type": "PRO", "belongs_level": 1},
  {"base_arc_curvature_radius": 8.65, "lens_type_number": 0.23, "lens_type": "PRO", "belongs_level": 1},
  {"base_arc_curvature_radius": 8.71, "lens_type_number": 0.23, "lens_type": "PRO", "belongs_level": 1},
  {"base_arc_curvature_radius": 8.77, "lens_type_number": 0.23, "lens_type": "PRO", "belongs_level": 1},
  {"base_arc_curvature_radius": 8.82, "lens_type_number": 0.23, "lens_type": "PRO", "belongs_level": 1},
  {"base_arc_curvature_radius": 8.88, "lens_type_number": 0.23, "lens_type": "PRO", "belongs_level": 1},
  {"base_arc_curvature_radius": 8.94, "lens_type_number": 0.23, "lens_type": "PRO", "belongs_level": 1},
  {"base_arc_curvature_radius": 9, "lens_type_number": 0.23, "lens_type": "PRO", "belongs_level": 1},
  {"base_arc_curvature_radius": 9.06, "lens_type_number": 0.23, "lens_type": "PRO", "belongs_level": 1},
  {"base_arc_curvature_radius": 9.12, "lens_type_number": 0.23, "lens_type": "PRO", "belongs_level": 1},
  {"base_arc_curvature_radius": 9.18, "lens_type_number": 0.23, "lens_type": "PRO", "belongs_level": 1},
  {"base_arc_curvature_radius": 9.25, "lens_type_number": 0.23, "lens_type": "PRO", "belongs_level": 1},
  {"base_arc_curvature_radius": 9.31, "lens_type_number": 0.23, "lens_type": "PRO", "belongs_level": 1},
  {"base_arc_curvature_radius": 9.38, "lens_type_number": 0.23, "lens_type": "PRO", "belongs_level": 1},
  {"base_arc_curvature_radius": 9.44, "lens_type_number": 0.23, "lens_type": "PRO", "belongs_level": 1},
  {"base_arc_curvature_radius": 9.51, "lens_type_number": 0.23, "lens_type": "PRO", "belongs_level": 1},
  {"base_arc_curvature_radius": 9.57, "lens_type_number": 0.23, "lens_type": "PRO", "belongs_level": 1},
  {"base_arc_curvature_radius": 9.64, "lens_type_number": 0.23, "lens_type": "PRO", "belongs_level": 1},
  {"base_arc_curvature_radius": 9.71, "lens_type_number": 0.23, "lens_type": "PRO", "belongs_level": 1},
  {"base_arc_curvature_radius": 9.78, "lens_type_number": 0.23, "lens_type": "PRO", "belongs_level": 1},
  {"base_arc_curvature_radius": 9.85, "lens_type_number": 0.23, "lens_type": "PRO", "belongs_level": 1},
  {"base_arc_curvature_radius": 9.93, "lens_type_number": 0.23, "lens_type": "PRO", "belongs_level": 1},
  {"base_arc_curvature_radius": 10, "lens_type_number": 0.23, "lens_type": "PRO", "belongs_level": 1},
  {"base_arc_curvature_radius": 10.08, "lens_type_number": 0.23, "lens_type": "PRO", "belongs_level": 1},
  {"base_arc_curvature_radius": 10.15, "lens_type_number": 0.23, "lens_type": "PRO", "belongs_level": 1},
  {"base_arc_curvature_radius": 10.23, "lens_type_number": 0.23, "lens_type": "PRO", "belongs_level": 1},
  {"base_arc_curvature_radius": 10.31, "lens_type_number": 0.23, "lens_type": "PRO", "belongs_level": 1},
  {"base_arc_curvature_radius": 10.39, "lens_type_number": 0.23, "lens_type": "PRO", "belongs_level": 1},
  {"base_arc_curvature_radius": 10.47, "lens_type_number": 0.23, "lens_type": "PRO", "belongs_level": 1},
  {"base_arc_curvature_radius": 10.55, "lens_type_number": 0.23, "lens_type": "PRO", "belongs_level": 1},
  {"base_arc_curvature_radius": 10.63, "lens_type_number": 0.23, "lens_type": "PRO", "belongs_level": 1},
  {"base_arc_curvature_radius": 10.71, "lens_type_number": 0.23, "lens_type": "PRO", "belongs_level": 1}
]
        pro_second_map=[
  {
    "base_arc_curvature_radius": 6.73,
    "lens_type_number": -2.5,
    "lens_type": "PRO",
    "belongs_level": 2
  },
  {
    "base_arc_curvature_radius": 6.777,
    "lens_type_number": -2.5,
    "lens_type": "PRO",
    "belongs_level": 2
  },
  {
    "base_arc_curvature_radius": 6.793,
    "lens_type_number": -2.5,
    "lens_type": "PRO",
    "belongs_level": 2
  },
  {
    "base_arc_curvature_radius": 6.876,
    "lens_type_number": -2.5,
    "lens_type": "PRO",
    "belongs_level": 2
  },
  {
    "base_arc_curvature_radius": 6.922,
    "lens_type_number": -2.5,
    "lens_type": "PRO",
    "belongs_level": 2
  },
  {
    "base_arc_curvature_radius": 6.965,
    "lens_type_number": -2.5,
    "lens_type": "PRO",
    "belongs_level": 2
  },
  {
    "base_arc_curvature_radius": 7.02,
    "lens_type_number": -2.5,
    "lens_type": "PRO",
    "belongs_level": 2
  },
  {
    "base_arc_curvature_radius": 7.065,
    "lens_type_number": -2.5,
    "lens_type": "PRO",
    "belongs_level": 2
  },
  {
    "base_arc_curvature_radius": 7.12,
    "lens_type_number": -2.5,
    "lens_type": "PRO",
    "belongs_level": 2
  },
  {
    "base_arc_curvature_radius": 7.18,
    "lens_type_number": -2.5,
    "lens_type": "PRO",
    "belongs_level": 2
  },
  {
    "base_arc_curvature_radius": 7.22,
    "lens_type_number": -2.5,
    "lens_type": "PRO",
    "belongs_level": 2
  },
  {
    "base_arc_curvature_radius": 7.273,
    "lens_type_number": -2.5,
    "lens_type": "PRO",
    "belongs_level": 2
  },
  {
    "base_arc_curvature_radius": 7.33,
    "lens_type_number": -2.5,
    "lens_type": "PRO",
    "belongs_level": 2
  },
  {
    "base_arc_curvature_radius": 7.373,
    "lens_type_number": -2.5,
    "lens_type": "PRO",
    "belongs_level": 2
  },
  {
    "base_arc_curvature_radius": 7.44,
    "lens_type_number": -2.5,
    "lens_type": "PRO",
    "belongs_level": 2
  },
  {
    "base_arc_curvature_radius": 7.293,
    "lens_type_number": -3.2,
    "lens_type": "PRO",
    "belongs_level": 2
  },
  {
    "base_arc_curvature_radius": 7.35,
    "lens_type_number": -3.2,
    "lens_type": "PRO",
    "belongs_level": 2
  },
  {
    "base_arc_curvature_radius": 7.405,
    "lens_type_number": -3.2,
    "lens_type": "PRO",
    "belongs_level": 2
  },
  {
    "base_arc_curvature_radius": 7.46,
    "lens_type_number": -3.2,
    "lens_type": "PRO",
    "belongs_level": 2
  },
  {
    "base_arc_curvature_radius": 7.527,
    "lens_type_number": -3.2,
    "lens_type": "PRO",
    "belongs_level": 2
  },
  {
    "base_arc_curvature_radius": 7.585,
    "lens_type_number": -3.2,
    "lens_type": "PRO",
    "belongs_level": 2
  },
  {
    "base_arc_curvature_radius": 7.64,
    "lens_type_number": -3.2,
    "lens_type": "PRO",
    "belongs_level": 2
  },
  {
    "base_arc_curvature_radius": 7.695,
    "lens_type_number": -3.2,
    "lens_type": "PRO",
    "belongs_level": 2
  },
  {
    "base_arc_curvature_radius": 7.76,
    "lens_type_number": -3.2,
    "lens_type": "PRO",
    "belongs_level": 2
  },
  {
    "base_arc_curvature_radius": 7.82,
    "lens_type_number": -3.2,
    "lens_type": "PRO",
    "belongs_level": 2
  },
  {
    "base_arc_curvature_radius": 7.885,
    "lens_type_number": -3.2,
    "lens_type": "PRO",
    "belongs_level": 2
  },
  {
    "base_arc_curvature_radius": 7.95,
    "lens_type_number": -3.2,
    "lens_type": "PRO",
    "belongs_level": 2
  },
  {
    "base_arc_curvature_radius": 7.828,
    "lens_type_number": -3.9,
    "lens_type": "PRO",
    "belongs_level": 2
  },
  {
    "base_arc_curvature_radius": 7.895,
    "lens_type_number": -3.9,
    "lens_type": "PRO",
    "belongs_level": 2
  },
  {
    "base_arc_curvature_radius": 7.963,
    "lens_type_number": -3.9,
    "lens_type": "PRO",
    "belongs_level": 2
  },
  {
    "base_arc_curvature_radius": 8.03,
    "lens_type_number": -3.9,
    "lens_type": "PRO",
    "belongs_level": 2
  },
  {
    "base_arc_curvature_radius": 8.1,
    "lens_type_number": -3.9,
    "lens_type": "PRO",
    "belongs_level": 2
  },
  {
    "base_arc_curvature_radius": 8.169,
    "lens_type_number": -3.9,
    "lens_type": "PRO",
    "belongs_level": 2
  },
  {
    "base_arc_curvature_radius": 8.23,
    "lens_type_number": 3.9,
    "lens_type": "PRO",
    "belongs_level": 2
  },
  {
    "base_arc_curvature_radius": 8.31,
    "lens_type_number": -3.9,
    "lens_type": "PRO",
    "belongs_level": 2
  },
  {
    "base_arc_curvature_radius": 8.376,
    "lens_type_number": -3.9,
    "lens_type": "PRO",
    "belongs_level": 2
  },
  {
    "base_arc_curvature_radius": 8.455,
    "lens_type_number": -3.9,
    "lens_type": "PRO",
    "belongs_level": 2
  },
  {
    "base_arc_curvature_radius": 8.52,
    "lens_type_number": -3.9,
    "lens_type": "PRO",
    "belongs_level": 2
  },
  {
    "base_arc_curvature_radius": 8.6,
    "lens_type_number": -3.9,
    "lens_type": "PRO",
    "belongs_level": 2
  },
  {
    "base_arc_curvature_radius": 8.454,
    "lens_type_number": -4.8,
    "lens_type": "PRO",
    "belongs_level": 2
  },
  {
    "base_arc_curvature_radius": 8.535,
    "lens_type_number": -4.8,
    "lens_type": "PRO",
    "belongs_level": 2
  },
  {
    "base_arc_curvature_radius": 8.61,
    "lens_type_number": -4.8,
    "lens_type": "PRO",
    "belongs_level": 2
  },
  {
    "base_arc_curvature_radius": 8.69,
    "lens_type_number": -4.8,
    "lens_type": "PRO",
    "belongs_level": 2
  },
  {
    "base_arc_curvature_radius": 8.765,
    "lens_type_number": -4.8,
    "lens_type": "PRO",
    "belongs_level": 2
  },
  {
    "base_arc_curvature_radius": 8.855,
    "lens_type_number": -4.8,
    "lens_type": "PRO",
    "belongs_level": 2
  },
  {
    "base_arc_curvature_radius": 8.94,
    "lens_type_number": -4.8,
    "lens_type": "PRO",
    "belongs_level": 2
  },
  {
    "base_arc_curvature_radius": 9.03,
    "lens_type_number": -4.8,
    "lens_type": "PRO",
    "belongs_level": 2
  },
  {
    "base_arc_curvature_radius": 9.1,
    "lens_type_number": -4.8,
    "lens_type": "PRO",
    "belongs_level": 2
  },
  {
    "base_arc_curvature_radius": 9.195,
    "lens_type_number": -4.8,
    "lens_type": "PRO",
    "belongs_level": 2
  },
  {
    "base_arc_curvature_radius": 9.285,
    "lens_type_number": -4.8,
    "lens_type": "PRO",
    "belongs_level": 2
  },
  {
    "base_arc_curvature_radius": 9.372,
    "lens_type_number": -4.8,
    "lens_type": "PRO",
    "belongs_level": 2
  },
  {
    "base_arc_curvature_radius": 9.46,
    "lens_type_number": -4.8,
    "lens_type": "PRO",
    "belongs_level": 2
  },
  {
    "base_arc_curvature_radius": 9.55,
    "lens_type_number": -4.8,
    "lens_type": "PRO",
    "belongs_level": 2
  },
  {
    "base_arc_curvature_radius": 9.64,
    "lens_type_number": -4.8,
    "lens_type": "PRO",
    "belongs_level": 2
  },
  {
    "base_arc_curvature_radius": 9.725,
    "lens_type_number": -4.8,
    "lens_type": "PRO",
    "belongs_level": 2
  }
]
        s_first_map = [
    {
        "base_arc_curvature_radius": 7.5,
        "lens_type_number": 0.23,
        "lens_type": "s",
        "belongs_level": 1
    },
    {
        "base_arc_curvature_radius": 7.54,
        "lens_type_number": 0.23,
        "lens_type": "s",
        "belongs_level": 1
    },
    {
        "base_arc_curvature_radius": 7.58,
        "lens_type_number": 0.23,
        "lens_type": "s",
        "belongs_level": 1
    },
    {
        "base_arc_curvature_radius": 7.63,
        "lens_type_number": 0.23,
        "lens_type": "s",
        "belongs_level": 1
    },
    {
        "base_arc_curvature_radius": 7.67,
        "lens_type_number": 0.23,
        "lens_type": "s",
        "belongs_level": 1
    },
    {
        "base_arc_curvature_radius": 7.71,
        "lens_type_number": 0.23,
        "lens_type": "s",
        "belongs_level": 1
    },
    {
        "base_arc_curvature_radius": 7.76,
        "lens_type_number": 0.23,
        "lens_type": "s",
        "belongs_level": 1
    },
    {
        "base_arc_curvature_radius": 7.8,
        "lens_type_number": 0.23,
        "lens_type": "s",
        "belongs_level": 1
    },
    {
        "base_arc_curvature_radius": 7.85,
        "lens_type_number": 0.23,
        "lens_type": "s",
        "belongs_level": 1
    },
    {
        "base_arc_curvature_radius": 7.9,
        "lens_type_number": 0.23,
        "lens_type": "s",
        "belongs_level": 1
    },
    {
        "base_arc_curvature_radius": 7.94,
        "lens_type_number": 0.23,
        "lens_type": "s",
        "belongs_level": 1
    },
    {
        "base_arc_curvature_radius": 7.99,
        "lens_type_number": 0.23,
        "lens_type": "s",
        "belongs_level": 1
    },
    {
        "base_arc_curvature_radius": 8.04,
        "lens_type_number": 0.23,
        "lens_type": "s",
        "belongs_level": 1
    },
    {
        "base_arc_curvature_radius": 8.08,
        "lens_type_number": 0.23,
        "lens_type": "s",
        "belongs_level": 1
    },
    {
        "base_arc_curvature_radius": 8.13,
        "lens_type_number": 0.23,
        "lens_type": "s",
        "belongs_level": 1
    },
    {
        "base_arc_curvature_radius": 8.18,
        "lens_type_number": 0.23,
        "lens_type": "s",
        "belongs_level": 1
    },
    {
        "base_arc_curvature_radius": 8.23,
        "lens_type_number": 0.23,
        "lens_type": "s",
        "belongs_level": 1
    },
    {
        "base_arc_curvature_radius": 8.28,
        "lens_type_number": 0.23,
        "lens_type": "s",
        "belongs_level": 1
    },
    {
        "base_arc_curvature_radius": 8.33,
        "lens_type_number": 0.23,
        "lens_type": "s",
        "belongs_level": 1
    },
    {
        "base_arc_curvature_radius": 8.39,
        "lens_type_number": 0.23,
        "lens_type": "s",
        "belongs_level": 1
    },
    {
        "base_arc_curvature_radius": 8.44,
        "lens_type_number": 0.23,
        "lens_type": "s",
        "belongs_level": 1
    },
    {
        "base_arc_curvature_radius": 8.49,
        "lens_type_number": 0.23,
        "lens_type": "s",
        "belongs_level": 1
    },
    {
        "base_arc_curvature_radius": 8.54,
        "lens_type_number": 0.23,
        "lens_type": "s",
        "belongs_level": 1
    },
    {
        "base_arc_curvature_radius": 8.6,
        "lens_type_number": 0.23,
        "lens_type": "s",
        "belongs_level": 1
    },
    {
        "base_arc_curvature_radius": 8.65,
        "lens_type_number": 0.23,
        "lens_type": "s",
        "belongs_level": 1
    },
    {
        "base_arc_curvature_radius": 8.71,
        "lens_type_number": 0.23,
        "lens_type": "s",
        "belongs_level": 1
    },
    {
        "base_arc_curvature_radius": 8.77,
        "lens_type_number": 0.23,
        "lens_type": "s",
        "belongs_level": 1
    },
    {
        "base_arc_curvature_radius": 8.82,
        "lens_type_number": 0.23,
        "lens_type": "s",
        "belongs_level": 1
    },
    {
        "base_arc_curvature_radius": 8.88,
        "lens_type_number": 0.23,
        "lens_type": "s",
        "belongs_level": 1
    },
    {
        "base_arc_curvature_radius": 8.94,
        "lens_type_number": 0.23,
        "lens_type": "s",
        "belongs_level": 1
    },
    {
        "base_arc_curvature_radius": 9,
        "lens_type_number": 0.23,
        "lens_type": "s",
        "belongs_level": 1
    },
    {
        "base_arc_curvature_radius": 9.06,
        "lens_type_number": 0.23,
        "lens_type": "s",
        "belongs_level": 1
    },
    {
        "base_arc_curvature_radius": 9.12,
        "lens_type_number": 0.23,
        "lens_type": "s",
        "belongs_level": 1
    },
    {
        "base_arc_curvature_radius": 9.18,
        "lens_type_number": 0.23,
        "lens_type": "s",
        "belongs_level": 1
    },
    {
        "base_arc_curvature_radius": 9.25,
        "lens_type_number": 0.23,
        "lens_type": "s",
        "belongs_level": 1
    },
    {
        "base_arc_curvature_radius": 9.31,
        "lens_type_number": 0.23,
        "lens_type": "s",
        "belongs_level": 1
    },
    {
        "base_arc_curvature_radius": 9.38,
        "lens_type_number": 0.23,
        "lens_type": "s",
        "belongs_level": 1
    },
    {
        "base_arc_curvature_radius": 9.44,
        "lens_type_number": 0.23,
        "lens_type": "s",
        "belongs_level": 1
    },
    {
        "base_arc_curvature_radius": 9.51,
        "lens_type_number": 0.23,
        "lens_type": "s",
        "belongs_level": 1
    },
    {
        "base_arc_curvature_radius": 9.57,
        "lens_type_number": 0.23,
        "lens_type": "s",
        "belongs_level": 1
    },
    {
        "base_arc_curvature_radius": 9.64,
        "lens_type_number": 0.23,
        "lens_type": "s",
        "belongs_level": 1
    },
    {
        "base_arc_curvature_radius": 9.71,
        "lens_type_number": 0.23,
        "lens_type": "s",
        "belongs_level": 1
    },
    {
        "base_arc_curvature_radius": 9.78,
        "lens_type_number": 0.23,
        "lens_type": "s",
        "belongs_level": 1
    },
    {
        "base_arc_curvature_radius": 9.85,
        "lens_type_number": 0.23,
        "lens_type": "s",
        "belongs_level": 1
    },
    {
        "base_arc_curvature_radius": 9.93,
        "lens_type_number": 0.23,
        "lens_type": "s",
        "belongs_level": 1
    },
    {
        "base_arc_curvature_radius": 10,
        "lens_type_number": 0.23,
        "lens_type": "s",
        "belongs_level": 1
    },
    {
        "base_arc_curvature_radius": 10.08,
        "lens_type_number": 0.23,
        "lens_type": "s",
        "belongs_level": 1
    },
    {
        "base_arc_curvature_radius": 10.15,
        "lens_type_number": 0.23,
        "lens_type": "s",
        "belongs_level": 1
    },
    {
        "base_arc_curvature_radius": 10.23,
        "lens_type_number": 0.23,
        "lens_type": "s",
        "belongs_level": 1
    },
    {
        "base_arc_curvature_radius": 10.31,
        "lens_type_number": 0.23,
        "lens_type": "s",
        "belongs_level": 1
    },
    {
        "base_arc_curvature_radius": 10.39,
        "lens_type_number": 0.23,
        "lens_type": "s",
        "belongs_level": 1
    },
    {
        "base_arc_curvature_radius": 10.47,
        "lens_type_number": 0.23,
        "lens_type": "s",
        "belongs_level": 1
    },
    {
        "base_arc_curvature_radius": 10.55,
        "lens_type_number": 0.23,
        "lens_type": "s",
        "belongs_level": 1
    },
    {
        "base_arc_curvature_radius": 10.63,
        "lens_type_number": 0.23,
        "lens_type": "s",
        "belongs_level": 1
    },
    {
        "base_arc_curvature_radius": 10.71,
        "lens_type_number": 0.23,
        "lens_type": "s",
        "belongs_level": 1
    }
]
        APlus_first_map = [
    {"base_arc_curvature_radius": 7.50, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A++"},
    {"base_arc_curvature_radius": 7.54, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A++"},
    {"base_arc_curvature_radius": 7.58, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A++"},
    {"base_arc_curvature_radius": 7.63, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A++"},
    {"base_arc_curvature_radius": 7.67, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A++"},
    {"base_arc_curvature_radius": 7.71, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A++"},
    {"base_arc_curvature_radius": 7.76, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A++"},
    {"base_arc_curvature_radius": 7.80, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A++"},
    {"base_arc_curvature_radius": 7.85, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A++"},
    {"base_arc_curvature_radius": 7.90, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A++"},
    {"base_arc_curvature_radius": 7.94, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A++"},
    {"base_arc_curvature_radius": 7.99, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A++"},
    {"base_arc_curvature_radius": 8.04, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A++"},
    {"base_arc_curvature_radius": 8.08, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A++"},
    {"base_arc_curvature_radius": 8.13, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A++"},
    {"base_arc_curvature_radius": 8.18, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A++"},
    {"base_arc_curvature_radius": 8.23, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A++"},
    {"base_arc_curvature_radius": 8.28, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A++"},
    {"base_arc_curvature_radius": 8.33, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A++"},
    {"base_arc_curvature_radius": 8.39, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A++"},
    {"base_arc_curvature_radius": 8.44, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A++"},
    {"base_arc_curvature_radius": 8.49, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A++"},
    {"base_arc_curvature_radius": 8.54, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A++"},
    {"base_arc_curvature_radius": 8.60, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A++"},
    {"base_arc_curvature_radius": 8.65, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A++"},
    {"base_arc_curvature_radius": 8.71, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A++"},
    {"base_arc_curvature_radius": 8.77, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A++"},
    {"base_arc_curvature_radius": 8.82, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A++"},
    {"base_arc_curvature_radius": 8.88, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A++"},
    {"base_arc_curvature_radius": 8.94, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A++"},
    {"base_arc_curvature_radius": 9.00, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A++"},
    {"base_arc_curvature_radius": 9.06, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A++"},
    {"base_arc_curvature_radius": 9.12, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A++"},
    {"base_arc_curvature_radius": 9.18, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A++"},
    {"base_arc_curvature_radius": 9.25, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A++"},
    {"base_arc_curvature_radius": 9.31, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A++"},
    {"base_arc_curvature_radius": 9.38, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A++"},
    {"base_arc_curvature_radius": 9.44, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A++"},
    {"base_arc_curvature_radius": 9.51, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A++"},
    {"base_arc_curvature_radius": 9.57, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A++"},
    {"base_arc_curvature_radius": 9.64, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A++"},
    {"base_arc_curvature_radius": 9.71, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A++"},
    {"base_arc_curvature_radius": 9.78, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A++"},
    {"base_arc_curvature_radius": 9.85, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A++"},
    {"base_arc_curvature_radius": 9.93, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A++"},
    {"base_arc_curvature_radius": 10.00, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A++"},
    {"base_arc_curvature_radius": 10.08, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A++"},
    {"base_arc_curvature_radius": 10.15, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A++"},
    {"base_arc_curvature_radius": 10.23, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A++"},
    {"base_arc_curvature_radius": 10.31, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A++"},
    {"base_arc_curvature_radius": 10.39, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A++"},
    {"base_arc_curvature_radius": 10.47, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A++"},
    {"base_arc_curvature_radius": 10.55, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A++"},
    {"base_arc_curvature_radius": 10.63, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A++"},
    {"base_arc_curvature_radius": 10.71, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A++"},
]
        APlus_second_map = [
    {"base_arc_curvature_radius": 3.759,  "lens_type_number": -13.0, "belongs_level": 2, "lens_type": "A++"},
    {"base_arc_curvature_radius": 3.838,  "lens_type_number": -13.0, "belongs_level": 2, "lens_type": "A++"},
    {"base_arc_curvature_radius": 3.916,  "lens_type_number": -13.0, "belongs_level": 2, "lens_type": "A++"},
    {"base_arc_curvature_radius": 4.012,  "lens_type_number": -13.0, "belongs_level": 2, "lens_type": "A++"},
    {"base_arc_curvature_radius": 4.086,  "lens_type_number": -13.0, "belongs_level": 2, "lens_type": "A++"},
    {"base_arc_curvature_radius": 4.162,  "lens_type_number": -13.0, "belongs_level": 2, "lens_type": "A++"},
    {"base_arc_curvature_radius": 4.253,  "lens_type_number": -13.0, "belongs_level": 2, "lens_type": "A++"},
    {"base_arc_curvature_radius": 4.327,  "lens_type_number": -13.0, "belongs_level": 2, "lens_type": "A++"},
    {"base_arc_curvature_radius": 4.416,  "lens_type_number": -13.0, "belongs_level": 2, "lens_type": "A++"},
    {"base_arc_curvature_radius": 4.504,  "lens_type_number": -13.0, "belongs_level": 2, "lens_type": "A++"},
    {"base_arc_curvature_radius": 4.574,  "lens_type_number": -13.0, "belongs_level": 2, "lens_type": "A++"},
    {"base_arc_curvature_radius": 4.66,   "lens_type_number": -13.0, "belongs_level": 2, "lens_type": "A++"},
    {"base_arc_curvature_radius": 4.005,  "lens_type_number": -15.0, "belongs_level": 2, "lens_type": "A++"},
    {"base_arc_curvature_radius": 4.085,  "lens_type_number": -15.0, "belongs_level": 2, "lens_type": "A++"},
    {"base_arc_curvature_radius": 4.1829, "lens_type_number": -15.0, "belongs_level": 2, "lens_type": "A++"},
    {"base_arc_curvature_radius": 4.279,  "lens_type_number": -15.0, "belongs_level": 2, "lens_type": "A++"},
    {"base_arc_curvature_radius": 4.3741, "lens_type_number": -15.0, "belongs_level": 2, "lens_type": "A++"},
    {"base_arc_curvature_radius": 4.467,  "lens_type_number": -15.0, "belongs_level": 2, "lens_type": "A++"},
    {"base_arc_curvature_radius": 4.5595, "lens_type_number": -15.0, "belongs_level": 2, "lens_type": "A++"},
    {"base_arc_curvature_radius": 4.668,  "lens_type_number": -15.0, "belongs_level": 2, "lens_type": "A++"},
    {"base_arc_curvature_radius": 4.757,  "lens_type_number": -15.0, "belongs_level": 2, "lens_type": "A++"},
    {"base_arc_curvature_radius": 4.846,  "lens_type_number": -15.0, "belongs_level": 2, "lens_type": "A++"},
    {"base_arc_curvature_radius": 4.225,  "lens_type_number": -17.0, "belongs_level": 2, "lens_type": "A++"},
    {"base_arc_curvature_radius": 4.3451, "lens_type_number": -17.0, "belongs_level": 2, "lens_type": "A++"},
    {"base_arc_curvature_radius": 4.4433, "lens_type_number": -17.0, "belongs_level": 2, "lens_type": "A++"},
    {"base_arc_curvature_radius": 4.57,   "lens_type_number": -17.0, "belongs_level": 2, "lens_type": "A++"},
    {"base_arc_curvature_radius": 4.6726, "lens_type_number": -17.0, "belongs_level": 2, "lens_type": "A++"},
    {"base_arc_curvature_radius": 4.7658, "lens_type_number": -17.0, "belongs_level": 2, "lens_type": "A++"},
    {"base_arc_curvature_radius": 4.8759, "lens_type_number": -17.0, "belongs_level": 2, "lens_type": "A++"},
    {"base_arc_curvature_radius": 4.9843, "lens_type_number": -17.0, "belongs_level": 2, "lens_type": "A++"},
    {"base_arc_curvature_radius": 4.4091, "lens_type_number": -19.0, "belongs_level": 2, "lens_type": "A++"},
    {"base_arc_curvature_radius": 4.53,   "lens_type_number": -19.0, "belongs_level": 2, "lens_type": "A++"},
    {"base_arc_curvature_radius": 4.649,  "lens_type_number": -19.0, "belongs_level": 2, "lens_type": "A++"},
    {"base_arc_curvature_radius": 4.765,  "lens_type_number": -19.0, "belongs_level": 2, "lens_type": "A++"},
    {"base_arc_curvature_radius": 4.899,  "lens_type_number": -19.0, "belongs_level": 2, "lens_type": "A++"},
    {"base_arc_curvature_radius": 5.012,  "lens_type_number": -19.0, "belongs_level": 2, "lens_type": "A++"},
    {"base_arc_curvature_radius": 5.138,  "lens_type_number": -19.0, "belongs_level": 2, "lens_type": "A++"},
    {"base_arc_curvature_radius": 5.249,  "lens_type_number": -19.0, "belongs_level": 2, "lens_type": "A++"},
    {"base_arc_curvature_radius": 5.374,  "lens_type_number": -19.0, "belongs_level": 2, "lens_type": "A++"},
    {"base_arc_curvature_radius": 5.48,   "lens_type_number": -19.0, "belongs_level": 2, "lens_type": "A++"},
    {"base_arc_curvature_radius": 4.653,  "lens_type_number": -22.0, "belongs_level": 2, "lens_type": "A++"},
    {"base_arc_curvature_radius": 4.796,  "lens_type_number": -22.0, "belongs_level": 2, "lens_type": "A++"},
    {"base_arc_curvature_radius": 4.936,  "lens_type_number": -22.0, "belongs_level": 2, "lens_type": "A++"},
    {"base_arc_curvature_radius": 5.074,  "lens_type_number": -22.0, "belongs_level": 2, "lens_type": "A++"},
    {"base_arc_curvature_radius": 5.227,  "lens_type_number": -22.0, "belongs_level": 2, "lens_type": "A++"},
    {"base_arc_curvature_radius": 5.359,  "lens_type_number": -22.0, "belongs_level": 2, "lens_type": "A++"},
    {"base_arc_curvature_radius": 5.507,  "lens_type_number": -22.0, "belongs_level": 2, "lens_type": "A++"},
    {"base_arc_curvature_radius": 5.634,  "lens_type_number": -22.0, "belongs_level": 2, "lens_type": "A++"},
    {"base_arc_curvature_radius": 5.777,  "lens_type_number": -22.0, "belongs_level": 2, "lens_type": "A++"},
    {"base_arc_curvature_radius": 5.917,  "lens_type_number": -22.0, "belongs_level": 2, "lens_type": "A++"},
    {"base_arc_curvature_radius": 6.056,  "lens_type_number": -22.0, "belongs_level": 2, "lens_type": "A++"},
    {"base_arc_curvature_radius": 6.192,  "lens_type_number": -22.0, "belongs_level": 2, "lens_type": "A++"},
    {"base_arc_curvature_radius": 6.326,  "lens_type_number": -22.0, "belongs_level": 2, "lens_type": "A++"},
    {"base_arc_curvature_radius": 6.459,  "lens_type_number": -22.0, "belongs_level": 2, "lens_type": "A++"},
    {"base_arc_curvature_radius": 6.59,   "lens_type_number": -22.0, "belongs_level": 2, "lens_type": "A++"},
]
        APlusPlus_second_map = [
    {"base_arc_curvature_radius": 6.357, "lens_type_number": -11.0, "belongs_level": 2, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 6.404, "lens_type_number": -11.0, "belongs_level": 2, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 6.451, "lens_type_number": -11.0, "belongs_level": 2, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 6.51,  "lens_type_number": -11.0, "belongs_level": 2, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 6.557, "lens_type_number": -11.0, "belongs_level": 2, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 6.603, "lens_type_number": -11.0, "belongs_level": 2, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 6.662, "lens_type_number": -11.0, "belongs_level": 2, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 6.708, "lens_type_number": -11.0, "belongs_level": 2, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 6.766, "lens_type_number": -11.0, "belongs_level": 2, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 6.824, "lens_type_number": -11.0, "belongs_level": 2, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 6.87,  "lens_type_number": -11.0, "belongs_level": 2, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 6.928, "lens_type_number": -11.0, "belongs_level": 2, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 6.777, "lens_type_number": -13.0, "belongs_level": 2, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 6.824, "lens_type_number": -13.0, "belongs_level": 2, "lens_type": "A+++"},  # 与上方 6.824(-11) 重复，将以后者为准
    {"base_arc_curvature_radius": 6.883, "lens_type_number": -13.0, "belongs_level": 2, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 6.942, "lens_type_number": -13.0, "belongs_level": 2, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 7.001, "lens_type_number": -13.0, "belongs_level": 2, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 7.06,  "lens_type_number": -13.0, "belongs_level": 2, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 7.118, "lens_type_number": -13.0, "belongs_level": 2, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 7.188, "lens_type_number": -13.0, "belongs_level": 2, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 7.247, "lens_type_number": -13.0, "belongs_level": 2, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 7.305, "lens_type_number": -13.0, "belongs_level": 2, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 7.165, "lens_type_number": -15.0, "belongs_level": 2, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 7.236, "lens_type_number": -15.0, "belongs_level": 2, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 7.295, "lens_type_number": -15.0, "belongs_level": 2, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 7.366, "lens_type_number": -15.0, "belongs_level": 2, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 7.437, "lens_type_number": -15.0, "belongs_level": 2, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 7.496, "lens_type_number": -15.0, "belongs_level": 2, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 7.567, "lens_type_number": -15.0, "belongs_level": 2, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 7.637, "lens_type_number": -15.0, "belongs_level": 2, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 7.518, "lens_type_number": -17.0, "belongs_level": 2, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 7.59,  "lens_type_number": -17.0, "belongs_level": 2, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 7.66,  "lens_type_number": -17.0, "belongs_level": 2, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 7.733, "lens_type_number": -17.0, "belongs_level": 2, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 7.816, "lens_type_number": -17.0, "belongs_level": 2, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 7.886, "lens_type_number": -17.0, "belongs_level": 2, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 7.969, "lens_type_number": -17.0, "belongs_level": 2, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 8.039, "lens_type_number": -17.0, "belongs_level": 2, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 8.122, "lens_type_number": -17.0, "belongs_level": 2, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 8.192, "lens_type_number": -17.0, "belongs_level": 2, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 8.008, "lens_type_number": -20.0, "belongs_level": 2, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 8.092, "lens_type_number": -20.0, "belongs_level": 2, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 8.176, "lens_type_number": -20.0, "belongs_level": 2, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 8.26,  "lens_type_number": -20.0, "belongs_level": 2, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 8.355, "lens_type_number": -20.0, "belongs_level": 2, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 8.438, "lens_type_number": -20.0, "belongs_level": 2, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 8.533, "lens_type_number": -20.0, "belongs_level": 2, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 8.615, "lens_type_number": -20.0, "belongs_level": 2, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 8.709, "lens_type_number": -20.0, "belongs_level": 2, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 8.803, "lens_type_number": -20.0, "belongs_level": 2, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 8.897, "lens_type_number": -20.0, "belongs_level": 2, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 8.99,  "lens_type_number": -20.0, "belongs_level": 2, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 9.083, "lens_type_number": -20.0, "belongs_level": 2, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 9.176, "lens_type_number": -20.0, "belongs_level": 2, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 9.268, "lens_type_number": -20.0, "belongs_level": 2, "lens_type": "A+++"},
]
        APlusPlus_first_map = [
    {"base_arc_curvature_radius": 7.50, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 7.54, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 7.58, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 7.63, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 7.67, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 7.71, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 7.76, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 7.80, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 7.85, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 7.90, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 7.94, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 7.99, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 8.04, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 8.08, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 8.13, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 8.18, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 8.23, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 8.28, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 8.33, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 8.39, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 8.44, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 8.49, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 8.54, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 8.60, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 8.65, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 8.71, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 8.77, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 8.82, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 8.88, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 8.94, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 9.00, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 9.06, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 9.12, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 9.18, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 9.25, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 9.31, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 9.38, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 9.44, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 9.51, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 9.57, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 9.64, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 9.71, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 9.78, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 9.85, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 9.93, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 10.00, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 10.08, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 10.15, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 10.23, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 10.31, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 10.39, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 10.47, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 10.55, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 10.63, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A+++"},
    {"base_arc_curvature_radius": 10.71, "lens_type_number": 0.0, "belongs_level": 1, "lens_type": "A+++"},
]

        # Combine both datasets
        all_data = a_first_map + a_second_map + pro_first_map + pro_second_map + s_first_map + APlus_first_map + APlus_second_map + APlusPlus_first_map + APlusPlus_second_map


        created_count = 0
        for item in all_data:
            # try:
            RelationshipTable.objects.create(
                base_arc_curvature_radius=item['base_arc_curvature_radius'],
                lens_type_number=item['lens_type_number'],
                belongs_level=item['belongs_level'],
                lens_type=item['lens_type']
            )
            created_count += 1
            # except Exception as e:
            #     self.stdout.write(self.style.ERROR(f'Error creating record: {e}'))

        logging.info("a,pro,s枚举表初始化成功")
        self.stdout.write(self.style.SUCCESS(f'Successfully created {created_count} records in RelationshipTable'))
