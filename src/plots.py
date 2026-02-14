import datetime
import pandas as pd
import sys
import matplotlib.pyplot as plt  # type: ignore
import numpy as np
from typing import List

# CI
efgreen         = "#005953"
eflightgreen    = "#69a3a2"
eflightergreen  = "#a2c5c4"
eflightestgreen = "#e6efee"


def parse_status_dict(status_dict: dict) -> tuple[int, int, int, int]:
    ''' Parse a single registration status dictionary.
    Missing values will be set to zero. '''

    new       = status_dict.get("new", 0)
    approved  = status_dict.get("approved", 0)
    partially = status_dict.get("partially paid", 0)
    paid      = status_dict.get("paid", 0)
    checkedin = status_dict.get("checked in", 0)
    return (new, approved, partially, paid, checkedin)


def parse_sponsor_dict(sponsor_dict: dict) -> tuple[int, int, int]:
    ''' Parse a single sponsor status dictionary.
    Missing values will be set to zero. '''

    normal       = sponsor_dict.get("normal", 0)
    contributor  = sponsor_dict.get("contributor", 0)
    sponsor      = sponsor_dict.get("sponsor", 0)
    supersponsor = sponsor_dict.get("supersponsor", 0)
    return (normal, contributor, sponsor, supersponsor)


def split_tuplecol(df: pd.core.frame.DataFrame,
                   incol: str,
                   outcols: List[str]) -> pd.core.frame.DataFrame:
    ''' Given a column of tuples, make a set of new columns,
        containing the tuple elements. Drop input column. '''

    # Sanity check: Make sure every element of the input column contains
    # an iterable with as many elements as we have output columns.
    if not all(df[incol].apply(len) == len(outcols)):
        sys.exit(f"split.tuplecol: Malformed entry in column {incol}.")
    
    for i, outcol in enumerate(outcols):
        df[outcol] = [x[i] for x in df[incol]]

    df.drop(columns = [incol], inplace = True)
    return df


def read_parse_input(filename: str = "./data/log.txt") -> pd.core.frame.DataFrame:
    # For now, we only need the time stamp, the total count (for sanity
    # checks), the reg status and the sponsor category column.
    try:
        df = pd.read_json(path_or_buf=filename, lines = True)
    except ValueError as e:
        sys.exit(f"read_parse_input: Error while loading source data: {e}")
    df = df.loc[:, ["CurrentDateTimeUtc", "TotalCount", "Status", "Sponsor"]]
    
    # Parse timestamp column via direct conversion
    df.CurrentDateTimeUtc = pd.to_datetime(df.CurrentDateTimeUtc)
    
    # Parse 'Status' and 'Sponsor' column from dicts to tuples.
    df.Status  = df.Status.apply(parse_status_dict)
    df.Sponsor = df.Sponsor.apply(parse_sponsor_dict)
    
    # Turn the two tuple columns into sets of individual columns.
    status_cols  = ["new", "approved", "partial", "paid", "checkedin"]
    sponsor_cols = ["normal", "contributor", "sponsor", "supersponsor"]
    df           = split_tuplecol(df      = df,
                                  incol   = "Status",
                                  outcols = status_cols)
    df           = split_tuplecol(df      = df,
                                  incol   = "Sponsor",
                                  outcols = sponsor_cols)
    
    return df


def daywise(df: pd.core.frame.DataFrame,
    offset: int) -> pd.core.frame.DataFrame:
    ''' Calculate day-wise count'''

    # Working copy
    out          = df.copy()

    # Get last count for every day
    out["Date"]  = pd.to_datetime(df['CurrentDateTimeUtc']).dt.strftime('%m/%d/%Y')
    out          = out.groupby("Date").agg("last").reset_index()
    out          = out.loc[:, ["Date", "TotalCount"]]
    
    # Add day index, shifted by offset of three,
    # s.t. day 0 is the day of reg opening
    out["idx"] = np.arange(0, len(out)) - offset

    return out


def makeplots(df: pd.core.frame.DataFrame,
              df_last: pd.core.frame.DataFrame,
              df_lastlast: pd.core.frame.DataFrame) -> None:

    ##################        
    # Prepare figure #
    ##################

    s = 20
    fig, axes = plt.subplots(nrows = 2, ncols = 2, figsize = (15,15))
    plt.subplots_adjust(hspace = .3, wspace=.3)
    for ax in axes.flat:
        ax.set_visible(False)

    #############
    # Left plot #
    #############

    ax           = axes.flat[0]
    ax.set_visible(True)

    df["totals"] = df.new + df.approved + df.partial + df.paid + df.checkedin
    
    # Comment in this block and change colours of the
    # other lines, once people can check in on-site
    #ax.plot(df.CurrentDateTimeUtc,
    #        df.checkedin,
    #        c      = efgreen,
    #        lw     = 2,
    #        marker = "",
    #        label  = "Checked in")
    
    ax.plot(df.CurrentDateTimeUtc,
            df.totals,
            c      = efgreen,
            lw     = 2,
            marker = "",
            label  = "Total")
    ax.plot(df.CurrentDateTimeUtc,
            df.paid + df.partial + df.checkedin,
            c      = eflightgreen,
            lw     = 2,
            marker = "",
            label  = "Paid (incl. partial)")

    # x axis
    ax.set_xlabel(xlabel   = "Time",
                  fontsize = s,
                  labelpad = 10)
    
    ax.set_xticks([datetime.date(2026, 1, 1),
                   datetime.date(2026, 2, 1),
                   datetime.date(2026, 3, 1),
                   datetime.date(2026, 4, 1),
                   datetime.date(2026, 5, 1),
                   datetime.date(2026, 6, 1),
                   datetime.date(2026, 7, 1),
                   datetime.date(2026, 8, 1),
                   datetime.date(2026, 9, 1)
                  ])
    ax.set_xticklabels(["Jan", "Feb", "Mar", "Apr",
                        "May", "Jun", "Jul", "Aug",
                        "Sep"])

    ax.tick_params(axis      = "x",
                   which     = "both",
                   labelsize = s,
                   pad       = 10)
    
    ax.set_xlim([datetime.date(2026, 2, 1),
                 datetime.date(2026, 4, 1)]) # target: 3rd Sept (2026, 8, 19)

    # y axis
    ax.set_ylabel(ylabel = "Count",
                  fontsize = s,
                  labelpad = 10)
    ax.set_yticks([0, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000])
    ax.hlines(y      = [1000 * i for i in range(50)],
              xmin   = datetime.date(2025, 1, 1),
              xmax   = datetime.date(2025, 10, 1),
              colors = "lightgrey",
              ls     = "-",
              lw     = 0.5)
    ax.tick_params(axis      = "y",
                   which     = "both",
                   labelsize = s,
                   pad       = 10)
    ax.set_ylim((0, 7000))
    
    # Legend
    ax.legend(loc      = 9,
              fontsize = 15,
              ncols    = 2,
              frameon  = False)


    ##############
    # Right plot #
    ##############

    ax = axes.flat[1]
    ax.set_visible(True)
    nb_normal      = df.iloc[-1,:].normal
    nb_contributor = df.iloc[-1,:].contributor
    nb_spons       = df.iloc[-1,:].sponsor
    nb_super       = df.iloc[-1,:].supersponsor
    nb_total       = nb_normal + nb_contributor + nb_spons + nb_super

    fr_normal      = nb_normal      / nb_total * 100
    fr_contributor = nb_contributor / nb_total * 100
    fr_spons       = nb_spons       / nb_total * 100
    fr_super       = nb_super       / nb_total * 100
                  
    
    ax.barh(y     = 0,
            width = fr_normal,
            color = eflightestgreen,
            label = "Normal")
    ax.barh(y     = 0,
            width = fr_contributor,
            left  = fr_normal,
            color = eflightergreen,
            label = "Contributor")
    ax.barh(y     = 0,
            width = fr_spons,
            left  = fr_normal + fr_contributor,
            color = eflightgreen,
            label = "Sponsor")
    ax.barh(y     = 0,
            width = fr_super,
            left  = fr_normal + fr_contributor + fr_spons,
            color = efgreen,
            label = "Supersponsor")

    # Year 2025
    ax.barh(y = 1,
            width = 63.8,
            color = eflightestgreen)
    ax.barh(y = 1,
            width = 19.9,
            left  = 63.8,
            color = eflightgreen)
    ax.barh(y = 1,
            width = 16.3,
            left  = 19.9 + 63.8,
            color = efgreen)

    # Year 2024
    ax.barh(y = 2,
            width = 73,
            color = eflightestgreen)
    ax.barh(y = 2,
            width = 16.3,
            left  = 73,
            color = eflightgreen)
    ax.barh(y = 2,
            width = 10.6,
            left  = 73 + 16.3,
            color = efgreen)
    
                  
    
    
    # x axis
    ax.set_xlabel(xlabel   = "Fraction [%]",
                  fontsize = s,
                  labelpad = 10)
    ax.tick_params(axis      = "x",
                   which     = "both",
                   labelsize = s,
                   pad       = 10)
    ax.tick_params(axis      = "y",
                   which     = "both",
                   labelsize = s,
                   pad       = 10)
    ax.set_xlim((0, 100))
 
    # y axis
    ax.set_ylabel(ylabel  = "")
    ax.set_ylim((-1.5, 4))
    ax.set_yticks([0, 1, 2])
    ax.set_yticklabels([2026, 2025, 2024])
    
    # Legend
    ax.legend(loc      = 9,
              fontsize = 15,
              ncols    = 2,
              frameon  = False)


    ####################
    # Bottom-left plot #
    ####################
        
    # We need daywise data for the bottom-left plot
    df_daywise          = daywise(df, offset = 4)
    df_last_daywise     = daywise(df_last, offset = 33)
    df_lastlast_daywise = daywise(df_lastlast, offset = 4)
    
    # Set up plot and plot the two time-courses
    ax = axes.flat[2]
    ax.set_visible(True)
    ax.plot(df_daywise.idx,
            df_daywise.TotalCount,
            lw     = 2,
            c      = efgreen,
            label  = "2026",
            zorder = 100)
    ax.plot(df_last_daywise.idx,
            df_last_daywise.TotalCount,
            lw    = 2,
            c     = eflightgreen,
            label = "2025")
    ax.plot(df_lastlast_daywise.idx,
            df_lastlast_daywise.TotalCount,
            lw    = 2,
            c     = eflightergreen,
            label = "2024")
    ax.vlines([192], 0, 10000, color = "grey", ls=":", label = "EF 2026 Begins")

    
    # x axis
    ax.set_xlabel(xlabel   = "Day After Reg Opening",
                  fontsize = s,
                  labelpad = 10)
    ax.tick_params(axis      = "x",
                   which     = "both",
                   labelsize = s,
                   pad       = 10)
    ax.set_xlim((-5, 250))
 
    # y axis
    ax.set_ylabel(ylabel  = "Total Regs",
                 fontsize = s,
                 labelpad = 10)
    ax.tick_params(axis      = "y",
                   which     = "both",
                   labelsize = s,
                   pad       = 10)
    ax.set_ylim((0, 8000))
    
    # Legend
    ax.legend(loc      = 8,
              fontsize = 15,
              ncols    = 1,
              frameon  = False)


    ###############
    # Annotations #
    ###############
    
    last     = str(df.CurrentDateTimeUtc.tolist()[-1]).split(".")[0]
 
    annot    = \
f'''Last update {last} (UTC).
For questions, contact @GermanCoyote.'''
    ax.annotate(text     = annot,
                xy       = (0.005, 0.005),
                xycoords = 'figure fraction',
                fontsize = s/3)

    # Upper-left plots
    new       = df.new.tolist()[-1]
    approved  = df.approved.tolist()[-1]
    partial   = df.partial.tolist()[-1]
    paid      = df.paid.tolist()[-1]
    checkedin = df.checkedin.tolist()[-1]
    total     = new + approved + partial + paid + checkedin
    annot     = \
f'''{nb_total} total regs, out of which {partial + paid} paid at least partially.'''
    axes.flat[0].annotate(text     = annot,
                          xy       = (0.005, 0.005),
                          xycoords = 'axes fraction',
                          fontsize = s/3)


    # Upper-right plots
    annot    = \
f'''{nb_normal} total regs ({nb_normal} normal, {nb_contributor} contributors, {nb_spons} sponsors, {nb_super} supersponsors).'''
    axes.flat[1].annotate(text     = annot,
                          xy       = (0.005, 0.005),
                          xycoords = 'axes fraction',
                          fontsize = s/3)

    #################    
    # Export figure #
    #################

    plt.savefig(fname       = "./out/Fig1.svg",
                bbox_inches = "tight")


if __name__ == "__main__":
    # This year's data, from our own logger
    ef2026 = read_parse_input("./data/log.txt")
    
    # Two last years
    ef2025 = pd.read_csv("./data/log2025_daywise.csv")
    ef2024 = pd.read_csv("./data/log2024_daywise.csv")
    
    makeplots(ef2026, ef2025, ef2024)
