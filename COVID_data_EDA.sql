/*
Covid 19 Data Exploration 

Skills used: Joins, CTE's, Temp Tables, Nested Querry, Windows Functions, Aggregate Functions, Creating Views, Converting Data Types
*/


SELECT *
FROM PortfolioProject..CovidDeaths
WHERE continent is not null
ORDER BY 3,4;


SELECT *
FROM PortfolioProject..CovidVaccination
WHERE continent is not null
ORDER BY 3,4;


-- SELECT DATA THAT WE ARE GOING TO BE USING
SELECT location, date, total_cases, new_cases, total_deaths, population
FROM PortfolioProject..CovidDeaths
WHERE continent is not null
ORDER BY 1,2;


-- CHECKING DATATYPES OF REQUIRED DATA 
USE PortfolioProject; -- Replace 'YourDatabaseName' with the name of your database
SELECT COLUMN_NAME, DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'CovidDeaths'
  AND COLUMN_NAME IN ('location', 'date', 'total_cases', 'new_cases', 'total_deaths', 'population');


-- CORRECTING DATATYPE OF REQUIRED DATA
USE PortfolioProject; -- Replace 'YourDatabaseName' with the name of your database
ALTER TABLE CovidDeaths
ALTER COLUMN total_cases float;
ALTER TABLE CovidDeaths
ALTER COLUMN total_deaths float;


-- LOOKING AT TOTAL CASES VS TOTAL DEATHS IN INDIA
-- Shows likelihood of dying if you get covid in INDIA
SELECT location, date, total_cases, total_deaths, (total_deaths/total_cases)*100 AS DeathPercentage 
FROM PortfolioProject..CovidDeaths
WHERE location like '%india%' and continent is not null 
ORDER BY 1,2


-- LOOKINNG AT TOTAL CASES VS POPULATION
-- Shows what percentage of population got covid
SELECT location, date, total_cases, population, (total_cases/population)*100 AS PercentPopulationInfected
FROM PortfolioProject..CovidDeaths
WHERE continent is not null
ORDER BY 1,2


-- LOOKING AT COUNTRIES WITH HIGHEST INFECTION RATE COMPARED TO POPULATION
SELECT location, population, MAX(total_cases) AS TotalInfectionCount, MAX((total_cases/population)*100) AS PercentPopulationInfected
FROM PortfolioProject..CovidDeaths
WHERE continent is not null
GROUP BY location, population
ORDER BY PercentPopulationInfected desc


-- SHOWING COUNRIES WITH TOTAL DEATH COUNT 
SELECT location, SUM(new_deaths) AS TotalDeathCount
FROM PortfolioProject..CovidDeaths
WHERE continent is not null
GROUP BY location
ORDER BY TotalDeathCount desc


-- LET'S BREAK THINGS DOWN BY CONTINENT
-- SHOWING CONTINENTS WITH TOTAL DEATH COUNT
SELECT subtable.continent, SUM(subtable.TotalDeathCountByCountry) AS TotalDeathCountByContinent
FROM (
	SELECT continent,location, MAX(total_deaths) AS TotalDeathCountByCountry 
	FROM PortfolioProject..CovidDeaths
	WHERE continent is not null
	GROUP BY continent,location
	)  AS subtable
GROUP BY subtable.continent
ORDER BY TotalDeathCountByContinent desc


-- GLOBAL NUMMBERS
SELECT SUM(new_cases) AS total_cases, SUM(new_deaths) AS total_deaths, (SUM(new_deaths)/SUM(new_cases))*100 AS DeathPercentage 
FROM PortfolioProject..CovidDeaths
WHERE continent is not null


-- SHOWING CUMMULATIVE GOLOBAL NUMBERS BY DATE
SELECT *, (newtemp.total_deaths/newtemp.total_cases)*100 AS DeathPercentage
FROM(
	SELECT temp.date, 
		   SUM(temp.new_cases) OVER (ORDER BY temp.date ASC) AS total_cases, 
		   SUM(temp.new_deaths) OVER (ORDER BY temp.date ASC) AS total_deaths
	FROM(
		SELECT date, NULLIF(SUM(new_cases),0) AS new_cases, NULLIF(SUM(new_deaths),0) AS new_deaths 
		FROM PortfolioProject..CovidDeaths
		WHERE continent is not null
		GROUP BY date
		) AS temp
	) AS newtemp
ORDER BY newtemp.date


-- Total Population vs Vaccinations
-- Shows Percentage of Population that has recieved at least one Covid Vaccine
SELECT dea.continent, dea.location, dea.date, dea.population, vac.new_vaccinations,
	   SUM(CAST(vac.new_vaccinations AS float)) OVER (PARTITION BY dea.location ORDER BY dea.location, dea.date) AS RollingPeopleVaccinated
FROM PortfolioProject..CovidDeaths AS dea
JOIN PortfolioProject..CovidVaccination AS vac
	ON dea.location = vac.location
	AND dea.date = vac.date
WHERE dea.continent IS NOT NULL;


-- Using CTE to perform Calculation on Partition By in previous query

WITH PopVsVac (continent, location, date, population, new_vaccinations, RollingPeopleVaccinated)
AS
(
SELECT dea.continent, dea.location, dea.date, dea.population, vac.new_vaccinations,
	   SUM(CAST(vac.new_vaccinations AS float)) OVER (PARTITION BY dea.location ORDER BY dea.location, dea.date) AS RollingPeopleVaccinated
FROM PortfolioProject..CovidDeaths AS dea
JOIN PortfolioProject..CovidVaccination AS vac
	ON dea.location = vac.location
	AND dea.date = vac.date
WHERE dea.continent IS NOT NULL
)
SELECT *, (RollingPeopleVaccinated/population)*100 AS PercentPeopleVaccinated
FROM PopVsVac;


-- Using Temp Table to perform Calculation on Partition By in previous query

DROP TABLE IF EXISTS #PercentPopulationVaccinated
CREATE TABLE #PercentPopulationVaccinated
(
continent nvarchar(255),
location nvarchar(255),
date datetime,
population float,
new_vaccinations float,
RollingPeopleVaccinated float
)

INSERT INTO #PercentPopulationVaccinated
SELECT dea.continent, dea.location, dea.date, dea.population, vac.new_vaccinations,
	   SUM(CAST(vac.new_vaccinations AS float)) OVER (PARTITION BY dea.location ORDER BY dea.location, dea.date) AS RollingPeopleVaccinated
FROM PortfolioProject..CovidDeaths AS dea
JOIN PortfolioProject..CovidVaccination AS vac
	ON dea.location = vac.location
	AND dea.date = vac.date
WHERE dea.continent IS NOT NULL;

SELECT *, (RollingPeopleVaccinated/population)*100 AS PercentPeopleVaccinated
FROM #PercentPopulationVaccinated



-- CREATING VIEW TO STORE DATA FOR LATER VISUALIZATIONS
CREATE VIEW GlobalNumbers AS
SELECT SUM(new_cases) AS total_cases, SUM(new_deaths) AS total_deaths, (SUM(new_deaths)/SUM(new_cases))*100 AS DeathPercentage 
FROM PortfolioProject..CovidDeaths
WHERE continent is not null;


CREATE VIEW DeathPercentage AS
SELECT *, (newtemp.total_deaths/newtemp.total_cases)*100 AS DeathPercentage
FROM(
	SELECT temp.date, 
		   SUM(temp.new_cases) OVER (ORDER BY temp.date ASC) AS total_cases, 
		   SUM(temp.new_deaths) OVER (ORDER BY temp.date ASC) AS total_deaths
	FROM(
		SELECT date, NULLIF(SUM(new_cases),0) AS new_cases, NULLIF(SUM(new_deaths),0) AS new_deaths 
		FROM PortfolioProject..CovidDeaths
		WHERE continent is not null
		GROUP BY date
		) AS temp
	) AS newtemp


CREATE VIEW TotalDeathCount AS
SELECT subtable.continent, SUM(subtable.TotalDeathCountByCountry) AS TotalDeathCountByContinent
FROM (
	SELECT continent,location, MAX(total_deaths) AS TotalDeathCountByCountry 
	FROM PortfolioProject..CovidDeaths
	WHERE continent is not null
	GROUP BY continent,location
	)  AS subtable
GROUP BY subtable.continent;


CREATE VIEW PercentPopulationInfected AS
SELECT location, population, MAX(total_cases) AS TotalInfectionCount, MAX((total_cases/population)*100) AS PercentPopulationInfected
FROM PortfolioProject..CovidDeaths
WHERE continent is not null
GROUP BY location, population;


CREATE VIEW PercentPopInfWithDate AS
SELECT location, population, date, MAX(total_cases) AS TotalInfectionCount, MAX((total_cases/population)*100) AS PercentPopulationInfected
FROM PortfolioProject..CovidDeaths
WHERE continent is not null
GROUP BY location, population, date


CREATE VIEW PercentPeopleVaccinated AS
WITH PopVsVac (continent, location, date, population, new_vaccinations, RollingPeopleVaccinated)
AS
(
SELECT dea.continent, dea.location, dea.date, dea.population, vac.new_vaccinations,
	   SUM(CAST(vac.new_vaccinations AS float)) OVER (PARTITION BY dea.location ORDER BY dea.location, dea.date) AS RollingPeopleVaccinated
FROM PortfolioProject..CovidDeaths AS dea
JOIN PortfolioProject..CovidVaccination AS vac
	ON dea.location = vac.location
	AND dea.date = vac.date
WHERE dea.continent IS NOT NULL
)
SELECT *, (RollingPeopleVaccinated/population)*100 AS PercentPeopleVaccinated
FROM PopVsVac;