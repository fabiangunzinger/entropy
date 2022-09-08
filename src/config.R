library(ggsci)
library(ggthemes)
library(ggthemr)
library(RColorBrewer)
library(scales)
library(wesanderson)


# Environment variable
Sys.setenv(AWS_PROFILE='3di', AWS_DEFAULT_REGION='eu-west-2')

# Global variables
ROOT <- '/Users/fgu/dev/projects/entropy'
FIGDIR <- file.path(ROOT, 'output/figures')
TABDIR <- file.path(ROOT, 'output/tables')

setwd(ROOT)


# Figure color scheme
palette <- pal_d3("category20c")(5) # ggsci
# palette <- brewer.pal(5, name = "Set1") # RColorBrewer
# palette <- wes_palette("IsleofDogs1") # wesanderson
# palette <- tableau_color_pal('Tableau 10')(5) # ggthemes
# palette <- ggthemr('camouflage', set_theme = FALSE)$palette$swatch # ggthemr
options(ggplot2.discrete.colour = palette)
options(ggplot2.discrete.fill = palette)

