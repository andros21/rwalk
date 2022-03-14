""" 1d random walker """

import sqlite3

import numpy as np
import pandas as pd
from numpy.linalg import norm

SQLITE3_DB = "/data/rwalker.sqlite3"


def classic_random_walker(init_site: int, limit: int, nsteps: int):
    """
    save two tables inside sqlite3 db:
        1. crw_pdf - row: nsteps+1, col: limit*2+1
        2. crw_std - row: nsteps+1, col: 1
    containg the results of 1-dim classic random walker simulation
    """
    # init pdf
    nsites = limit * 2 + 1
    pdf = np.zeros((nsteps + 1, nsites))
    pdf[0][init_site + limit] = 1.0
    # evolve pdf
    for i in np.arange(1, pdf.shape[0], 1):
        for j in np.arange(1, pdf.shape[1] - 1, 1):
            pdf[i][j] = 0.5 * pdf[i - 1][j - 1] + 0.5 * pdf[i - 1][j + 1]
    # compute std
    sites = np.arange(-limit, limit + 1, 1)
    var = pdf @ sites**2
    std = np.sqrt(var)
    # save tables
    pdf_df = pd.DataFrame(pdf)
    std_df = pd.DataFrame(std.T)
    engine = sqlite3.connect(SQLITE3_DB)
    pdf_df.to_sql("crw_pdf", engine, if_exists="replace", index=False)
    std_df.to_sql("crw_std", engine, if_exists="replace", index=False)
    engine.close()


def quantum_random_walker(init_site: int, limit: int, nsteps: int):
    """
    save two tables inside sqlite3 db:
        1. qrw_pdf - row: nsteps+1, col: limit*2+1
        2. qrw_std - row: nsteps+1, col: 1
    containg the results of 1-dim quantum random walker simulation
    """
    # init pdf
    nsites = limit * 2 + 1
    pdf = np.zeros((nsteps + 1, nsites))
    wave_0 = np.zeros((nsteps + 1, nsites), dtype=complex)
    wave_1 = np.zeros((nsteps + 1, nsites), dtype=complex)
    wave_0[0][init_site + limit] = 1.0 / np.sqrt(2)
    wave_1[0][init_site + limit] = -1.0j / np.sqrt(2)
    pdf[0][init_site + limit] = (
        norm(wave_0[0][init_site + limit]) ** 2
        + norm(wave_1[0][init_site + limit]) ** 2
    )
    # evolve pdf
    for i in np.arange(1, pdf.shape[0], 1):
        for j in np.arange(1, pdf.shape[1] - 1, 1):
            wave_0[i][j] = (wave_0[i - 1][j - 1] + wave_1[i - 1][j - 1]) / np.sqrt(2)
            wave_1[i][j] = (wave_0[i - 1][j + 1] - wave_1[i - 1][j + 1]) / np.sqrt(2)
            pdf[i][j] = norm(wave_0[i][j]) ** 2 + norm(wave_1[i][j]) ** 2
    # compute std
    sites = np.arange(-limit, limit + 1, 1)
    var = pdf @ sites**2
    std = np.sqrt(var)
    # save tables
    pdf_df = pd.DataFrame(pdf)
    std_df = pd.DataFrame(std.T)
    engine = sqlite3.connect(SQLITE3_DB)
    pdf_df.to_sql("qrw_pdf", engine, if_exists="replace", index=False)
    std_df.to_sql("qrw_std", engine, if_exists="replace", index=False)
    engine.close()


if __name__ == "__main__":
    classic_random_walker(0, 50, 100)
    quantum_random_walker(0, 80, 100)
