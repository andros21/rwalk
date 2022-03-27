#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gzip
import json
import os
import re
import sqlite3
import sys

import networkx as nx
import numpy as np
import pandas as pd
import scipy.linalg as la

# data dirs
if os.path.exists("/data"):
    DATA_DIR = "/data"
    SQLITE3_DB = os.path.join(DATA_DIR, "rwalker.sqlite3")
else:
    DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    SQLITE3_DB = os.path.join(DATA_DIR, "rwalker.sqlite3")
    os.makedirs(DATA_DIR, exist_ok=True)


def _die(msg: str):
    """print error and exit 1"""
    print(msg, file=sys.stderr)
    sys.exit(1)


def _dump_to_sql(dataframes: list, tables: list):
    """save input dataframes as tables inside salite3 db"""
    engine = sqlite3.connect(SQLITE3_DB)
    for df, table in zip(dataframes, tables):
        df.to_sql(table, engine, if_exists="replace", index=False)
    engine.close()


def _fix_cyto_json(graph: str, cyto_json: dict) -> dict:
    """fix cytoscape json dictionary"""
    if graph == "line":
        for node in cyto_json["elements"]["nodes"]:
            node["data"]["name"] = str(
                int(node["data"]["name"])
                - (len(cyto_json["elements"]["nodes"]) - 1) * 0.5
            )
    cyto_str = json.dumps(cyto_json)
    cyto_str = re.sub(r'"source":\ (\d?\d?\d)', r'"source": "\1"', cyto_str)
    cyto_str = re.sub(r'"target":\ (\d?\d?\d)', r'"target": "\1"', cyto_str)
    return json.loads(cyto_str)


def _gen_laplacian_matrix(
    graph: str, dim: int, walker: str, time: str, draw=True
) -> np.ndarray:
    """
    generate laplacian matrix of given graph and dim,
    and if draw is True save the graph as cytoscape json format
    """
    A = np.zeros((dim, dim))
    if graph == "line":
        for i in np.arange(A.shape[0]):
            for j in np.arange(A.shape[1]):
                if ((j == i - 1) and (i - 1 >= 0)) or (
                    (j == i + 1) and (i + 1 < A.shape[0])
                ):
                    A[i][j] = 1.0
    elif graph == "ring":
        for i in np.arange(A.shape[0]):
            for j in np.arange(A.shape[1]):
                if ((j == i - 1) and (i - 1 >= 0)) or (
                    (j == i + 1) and (i + 1 < A.shape[0])
                ):
                    A[i][j] = 1.0
        A[0][dim - 1] = 1.0
        A[dim - 1][0] = 1.0
    elif graph == "rand":
        G = nx.random_regular_graph(2, dim, seed=0)
        A = nx.to_numpy_array(G)
    else:
        _die(f"[ERROR] {graph} graph not planned to be implemented")
    if not np.allclose(A, A.T, rtol=1e-5, atol=1e-8):
        _die(f"[ERROR] adjacency matrix for {graph} graph it's not symmetric")
    if draw:
        G = nx.from_numpy_matrix(A)
        cyto_json = nx.cytoscape_data(G)
        cyto_json = _fix_cyto_json(graph, cyto_json)
        with gzip.open(
            os.path.join(DATA_DIR, f"{walker}-{graph}-{time}.json.gz"),
            "wt",
            encoding="UTF-8",
        ) as gz:
            json.dump(cyto_json, gz)
    return np.diag(np.sum(A, axis=0)) - A


def classic_dtime(graph: str, init_site: int, limit: int, nsteps: int):
    """
    save two tables inside sqlite3 db:
        1. crw_pdf - row: nsteps+1, col: limit*2+1
        2. crw_std - row: nsteps+1, col: 1
    containg the results of:
        classic random walker discrete-time on-graph simulation
    save the graph rappresentation as cytoscape compressed json
    """
    # parameters
    if graph == "line":
        nsites = limit * 2 + 1
        sites = np.arange(-limit, limit + 1, 1)
    elif graph == "ring":
        nsites = limit + 1
        sites = np.arange(0, limit + 1, 1)
    else:
        _die(f"[ERROR] {graph} graph not planned to be implemented")
    # init pdf
    pdf = np.zeros((nsteps + 1, nsites))
    if graph == "line":
        init_idx = init_site + limit
    else:
        init_idx = init_site
    pdf[0][init_idx] = 1.0
    # evolve pdf
    if graph == "line":
        for i in np.arange(1, pdf.shape[0], 1):
            for j in np.arange(0, pdf.shape[1], 1):
                if j + 1 >= pdf.shape[1]:
                    pdf[i][j] = 1.0 * pdf[i - 1][j - 1]
                elif j - 1 < 0:
                    pdf[i][j] = 1.0 * pdf[i - 1][j + 1]
                else:
                    pdf[i][j] = 0.5 * pdf[i - 1][j - 1] + 0.5 * pdf[i - 1][j + 1]
    else:
        for i in np.arange(1, pdf.shape[0], 1):
            for j in np.arange(0, pdf.shape[1], 1):
                if j - 1 == -1:
                    pdf[i][j] = 0.5 * pdf[i - 1][limit] + 0.5 * pdf[i - 1][j + 1]
                elif j + 1 == limit + 1:
                    pdf[i][j] = 0.5 * pdf[i - 1][j - 1] + 0.5 * pdf[i - 1][0]
                else:
                    pdf[i][j] = 0.5 * pdf[i - 1][j - 1] + 0.5 * pdf[i - 1][j + 1]
    # draw graph
    _gen_laplacian_matrix(graph, nsites, "classic", "discrete")
    # compute std
    if graph == "ring":
        sites = np.concatenate(
            (np.arange(0, int(limit * 0.5) + 1, 1), np.arange(-int(limit * 0.5), 0, 1))
        )
    var = pdf @ sites**2
    std = np.sqrt(var)
    # save tables
    pdf_df = pd.DataFrame(pdf)
    std_df = pd.DataFrame(std.T)
    _dump_to_sql([pdf_df, std_df], [f"crw_{graph}_pdf", f"crw_{graph}_std"])


def classic_ctime(graph: str, init_site: int, limit: int, nsteps: int):
    """
    save two tables inside sqlite3 db:
        1. crw_ct_pdf - row: nsteps+1, col: limit*2+1
        2. crw_ct_std - row: nsteps+1, col: 1
    containg the results of:
        classic random walker continuous-time on-graph simulation
    save the graph rappresentation as cytoscape compressed json
    """
    # parameters
    gamma = 0.15
    times = np.linspace(0, nsteps + 1, nsteps + 1)
    if graph == "line":
        nsites = limit * 2 + 1
        sites = np.arange(-limit, limit + 1, 1)
    elif graph == "ring" or graph == "rand":
        nsites = limit + 1
        sites = np.arange(0, limit + 1, 1)
    else:
        _die(f"[ERROR] {graph} graph not planned to be implemented")
    # evolve matrix
    H = gamma * _gen_laplacian_matrix(graph, nsites, "classic", "continuous")
    # init pdf
    pdf = np.zeros((times.size, nsites))
    if graph == "line":
        init_idx = init_site + limit
    else:
        init_idx = init_site
    pdf[0][init_idx] = 1.0
    # evolve pdf
    for i, time in enumerate(times[1:]):
        pdf[i + 1] = la.expm(-time * H) @ pdf[0]
    # compute std
    if graph == "ring":
        sites = np.concatenate(
            (np.arange(0, int(limit * 0.5) + 1, 1), np.arange(-int(limit * 0.5), 0, 1))
        )
    var = pdf @ sites**2 if not graph == "rand" else None
    std = np.sqrt(var) if not graph == "rand" else None
    # save tables
    pdf_df = pd.DataFrame(pdf)
    std_df = pd.DataFrame(std.T) if not graph == "rand" else None
    if not graph == "rand":
        _dump_to_sql([pdf_df, std_df], [f"crw_{graph}_ct_pdf", f"crw_{graph}_ct_std"])
    else:
        _dump_to_sql([pdf_df, std_df], [f"crw_{graph}_ct_pdf"])


def quantum_dtime(graph: str, init_site: int, limit: int, nsteps: int):
    """
    save two tables inside sqlite3 db:
        1. qrw_pdf - row: nsteps+1, col: limit*2+1
        2. qrw_std - row: nsteps+1, col: 1
    containg the results of:
        quantum random walker discrete-time on-graph simulation
    save the graph rappresentation as cytoscape compressed json
    """
    # parameters
    if graph == "line":
        nsites = limit * 2 + 1
        sites = np.arange(-limit, limit + 1, 1)
    elif graph == "ring":
        nsites = limit + 1
        sites = np.arange(0, limit + 1, 1)
    else:
        _die(f"[ERROR] {graph} graph not planned to be implemented")
    # init pdf
    pdf = np.zeros((nsteps + 1, nsites))
    wave_0 = np.zeros((nsteps + 1, nsites), dtype=complex)
    wave_1 = np.zeros((nsteps + 1, nsites), dtype=complex)
    if graph == "line":
        init_idx = init_site + limit
    else:
        init_idx = init_site
    wave_0[0][init_idx] = 1.0 / np.sqrt(2)
    wave_1[0][init_idx] = -1.0j / np.sqrt(2)
    pdf[0][init_idx] = (
        la.norm(wave_0[0][init_idx]) ** 2 + la.norm(wave_1[0][init_idx]) ** 2
    )
    # evolve pdf
    if graph == "line":
        for i in np.arange(1, pdf.shape[0], 1):
            for j in np.arange(1, pdf.shape[1] - 1, 1):
                wave_0[i][j] = (wave_0[i - 1][j - 1] + wave_1[i - 1][j - 1]) / np.sqrt(
                    2
                )
                wave_1[i][j] = (wave_0[i - 1][j + 1] - wave_1[i - 1][j + 1]) / np.sqrt(
                    2
                )
                pdf[i][j] = la.norm(wave_0[i][j]) ** 2 + la.norm(wave_1[i][j]) ** 2
    else:
        for i in np.arange(1, pdf.shape[0], 1):
            for j in np.arange(0, pdf.shape[1], 1):
                if j - 1 == -1:
                    wave_0[i][j] = (
                        wave_0[i - 1][limit] + wave_1[i - 1][limit]
                    ) / np.sqrt(2)
                    wave_1[i][j] = (
                        wave_0[i - 1][j + 1] - wave_1[i - 1][j + 1]
                    ) / np.sqrt(2)
                elif j + 1 == limit + 1:
                    wave_0[i][j] = (
                        wave_0[i - 1][j - 1] + wave_1[i - 1][j - 1]
                    ) / np.sqrt(2)
                    wave_1[i][j] = (wave_0[i - 1][0] - wave_1[i - 1][0]) / np.sqrt(2)
                else:
                    wave_0[i][j] = (
                        wave_0[i - 1][j - 1] + wave_1[i - 1][j - 1]
                    ) / np.sqrt(2)
                    wave_1[i][j] = (
                        wave_0[i - 1][j + 1] - wave_1[i - 1][j + 1]
                    ) / np.sqrt(2)
                pdf[i][j] = la.norm(wave_0[i][j]) ** 2 + la.norm(wave_1[i][j]) ** 2
    # draw graph
    _gen_laplacian_matrix(graph, nsites, "quantum", "discrete")
    # compute std
    if graph == "ring":
        sites = np.concatenate(
            (np.arange(0, int(limit * 0.5) + 1, 1), np.arange(-int(limit * 0.5), 0, 1))
        )
    var = pdf @ sites**2
    std = np.sqrt(var)
    # save tables
    pdf_df = pd.DataFrame(pdf)
    std_df = pd.DataFrame(std.T)
    _dump_to_sql([pdf_df, std_df], [f"qrw_{graph}_pdf", f"qrw_{graph}_std"])


def quantum_ctime(graph: str, init_site: int, limit: int, nsteps: int):
    """
    save two tables inside sqlite3 db:
        1. qrw_pdf - row: nsteps+1, col: limit*2+1
        2. qrw_std - row: nsteps+1, col: 1
    containg the results of:
        quantum random walker continuous-time on-graph simulation
    save the graph rappresentation as cytoscape compressed json
    """
    # parameters
    gamma = 0.35
    times = np.linspace(0, nsteps + 1, nsteps + 1)
    if graph == "line":
        nsites = limit * 2 + 1
        sites = np.arange(-limit, limit + 1, 1)
    elif graph == "ring" or graph == "rand":
        nsites = limit + 1
        sites = np.arange(0, limit + 1, 1)
    else:
        _die(f"[ERROR] {graph} graph not planned to be implemented")
    # evolution matrix
    H = gamma * _gen_laplacian_matrix(graph, nsites, "quantum", "continuous")
    eig_vals, eig_vecs = la.eigh(H)
    # init pdf
    pdf = np.zeros((times.size, nsites))
    if graph == "line":
        init_idx = init_site + limit
    else:
        init_idx = init_site
    pdf[0][init_idx] = 1.0
    # evolve pdf
    aj = np.empty(eig_vals.size, dtype=complex)
    for i, time in enumerate(times[1:]):
        for j in np.arange(0, pdf.shape[1], 1):
            for k, (eig_val, eig_vec) in enumerate(zip(eig_vals, eig_vecs)):
                aj[k] = (
                    np.exp(-1.0j * eig_val * time, dtype=complex)
                    * np.conj(eig_vec[init_idx])
                    * eig_vec[j]
                )
            pdf[i + 1][j] = la.norm(np.sum(aj)) ** 2
    # compute std
    if graph == "ring":
        sites = np.concatenate(
            (np.arange(0, int(limit * 0.5) + 1, 1), np.arange(-int(limit * 0.5), 0, 1))
        )
    var = pdf @ sites**2 if not graph == "rand" else None
    std = np.sqrt(var) if not graph == "rand" else None
    # save tables
    pdf_df = pd.DataFrame(pdf)
    std_df = pd.DataFrame(std.T) if not graph == "rand" else None
    if not graph == "rand":
        _dump_to_sql([pdf_df, std_df], [f"qrw_{graph}_ct_pdf", f"qrw_{graph}_ct_std"])
    else:
        _dump_to_sql([pdf_df, std_df], [f"qrw_{graph}_ct_pdf"])


if __name__ == "__main__":
    classic_dtime("line", 0, 50, 100)
    classic_dtime("ring", 0, 100, 100)

    quantum_dtime("line", 0, 80, 100)
    quantum_dtime("ring", 0, 160, 100)

    classic_ctime("line", 0, 50, 100)
    classic_ctime("ring", 0, 100, 100)
    classic_ctime("rand", 0, 100, 100)

    quantum_ctime("line", 0, 80, 100)
    quantum_ctime("ring", 0, 200, 100)
    quantum_ctime("rand", 0, 100, 100)
