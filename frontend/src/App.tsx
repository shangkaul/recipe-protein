import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import {
  ArrowLeft,
  ArrowRight,
  Check,
  Clock3,
  Leaf,
  Search,
  SlidersHorizontal,
  Sparkles,
  Target,
  Utensils,
  X,
} from 'lucide-react'
import './App.css'
import { adaptRecipe, confirmRecipeNutrition, getFeatured, getRecipe, searchRecipes } from './services/api'
import type { AdaptationResult, ConfirmedNutrition, RecipeDetail, RecipeSummary, SearchResponse } from './types/recipe'

const categories = [
  { value: 'all', label: 'For you' },
  { value: 'main', label: 'Main meals' },
  { value: 'soup', label: 'Soups' },
  { value: 'salad', label: 'Salads' },
  { value: 'snack', label: 'Small bites' },
]

function App() {
  const [featured, setFeatured] = useState<RecipeSummary[]>([])
  const [results, setResults] = useState<SearchResponse | null>(null)
  const [detail, setDetail] = useState<RecipeDetail | null>(null)
  const [category, setCategory] = useState('all')
  const [pantryOpen, setPantryOpen] = useState(false)
  const [pantry, setPantry] = useState(localStorage.getItem('protein-pantry:pantry') || '')
  const [target, setTarget] = useState(Number(localStorage.getItem('protein-pantry:target')) || 30)
  const [maxMinutes, setMaxMinutes] = useState<number | ''>('')
  const [exclusions, setExclusions] = useState(localStorage.getItem('protein-pantry:exclusions') || '')
  const [loading, setLoading] = useState(true)
  const [searching, setSearching] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let current = true
    getFeatured(category)
      .then((recipes) => {
        if (!current) return
        setFeatured(recipes)
        localStorage.setItem(`protein-pantry:featured:${category}`, JSON.stringify(recipes))
        setError(null)
      })
      .catch((requestError: Error) => {
        const cached = localStorage.getItem(`protein-pantry:featured:${category}`)
        if (cached) setFeatured(JSON.parse(cached))
        setError(cached ? 'Showing saved meal ideas. Reconnect to search your pantry.' : requestError.message)
      })
      .finally(() => current && setLoading(false))
    return () => { current = false }
  }, [category])

  async function submitSearch(event: FormEvent) {
    event.preventDefault()
    setSearching(true)
    setError(null)
    localStorage.setItem('protein-pantry:pantry', pantry)
    localStorage.setItem('protein-pantry:target', String(target))
    localStorage.setItem('protein-pantry:exclusions', exclusions)
    try {
      setResults(await searchRecipes({
        text: pantry,
        protein_target_g: target,
        preferred_minutes: maxMinutes === '' ? null : maxMinutes,
        exclusions: exclusions
          .split(/[,;\n]+|\band\b/i)
          .map((value) => value.trim())
          .filter(Boolean),
      }))
      setPantryOpen(false)
      window.scrollTo({ top: 0, behavior: 'smooth' })
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Search is unavailable.')
    } finally {
      setSearching(false)
    }
  }

  async function openRecipe(slug: string) {
    setError(null)
    try {
      setDetail(await getRecipe(slug))
      document.body.classList.add('detail-is-open')
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Recipe details are unavailable.')
    }
  }

  function closeRecipe() {
    setDetail(null)
    document.body.classList.remove('detail-is-open')
  }

  function resetBrowse() {
    setResults(null)
    setCategory('all')
  }

  const displayed = results?.results || featured
  const exclusionList = exclusions
    .split(/[,;\n]+|\band\b/i)
    .map((value) => value.trim())
    .filter(Boolean)

  return (
    <div className="app-shell">
      <header className="app-bar">
        <button className="brand" type="button" onClick={resetBrowse} aria-label="Protein Pantry home">
          <span className="brand-mark"><Leaf size={19} strokeWidth={2.4} /></span>
          <span>Protein Pantry</span>
        </button>
        <span className="privacy-note"><span className="status-dot" /> Stays on your device</span>
      </header>

      <main className="workspace">
        <aside className={`pantry-panel ${pantryOpen ? 'is-open' : ''}`} aria-label="Pantry search">
          <div className="pantry-panel-heading">
            <div>
              <h2>Cook with what you have</h2>
              <p>Tell us what is in the kitchen. Everyday words are fine.</p>
            </div>
            <button className="icon-button mobile-only" type="button" onClick={() => setPantryOpen(false)} aria-label="Close pantry search">
              <X size={21} />
            </button>
          </div>
          <form onSubmit={submitSearch}>
            <label htmlFor="pantry">Your ingredients</label>
            <textarea
              id="pantry"
              value={pantry}
              onChange={(event) => setPantry(event.target.value)}
              placeholder="e.g. eggs, leftover rice, spinach, chicken"
              rows={4}
              required
            />

            <div className="field-row">
              <div>
                <label htmlFor="protein">Protein per meal</label>
                <div className="input-with-unit">
                  <input id="protein" type="number" min="5" max="100" value={target} onChange={(event) => setTarget(Number(event.target.value))} />
                  <span>g</span>
                </div>
              </div>
              <div>
                <label htmlFor="time">Preferred cooking time</label>
                <div className="input-with-unit">
                  <input id="time" type="number" min="5" max="240" step="5" value={maxMinutes} placeholder="Any" onChange={(event) => setMaxMinutes(event.target.value === '' ? '' : Number(event.target.value))} />
                  <span>{maxMinutes === '' ? '' : 'min'}</span>
                </div>
              </div>
            </div>

            <label className="exclusions-label" htmlFor="exclusions">Avoid ingredients <span>(optional)</span></label>
            <input
              id="exclusions"
              type="text"
              value={exclusions}
              onChange={(event) => setExclusions(event.target.value)}
              placeholder="e.g. mushrooms, peanuts, coconut"
            />
            <p className="field-help">Separate several ingredients with commas. Red meat is always excluded.</p>

            <p className="form-note"><Target size={16} /> You choose the target. We do not provide medical advice.</p>
            <button className="primary-button" type="submit" disabled={searching || !pantry.trim()}>
              {searching ? 'Finding meals…' : 'Find meals'}
              {!searching && <Search size={19} />}
            </button>
          </form>
        </aside>

        <section className="meal-workspace" aria-live="polite">
          <div className="section-heading">
            <div>
              {results ? (
                <button className="back-link" type="button" onClick={resetBrowse}><ArrowLeft size={17} /> Browse all ideas</button>
              ) : null}
              <h1>{results ? 'Meals that fit your pantry' : 'What sounds good?'}</h1>
              <p>
                {results
                  ? `${results.results.length} choices ranked by pantry fit${maxMinutes === '' ? '' : `, closeness to ${maxMinutes} minutes`}, and your ${target}g protein target.`
                  : 'Start with an idea, then make it work with what is already in your kitchen.'}
              </p>
            </div>
            <button className="pantry-trigger" type="button" onClick={() => setPantryOpen(true)}>
              <SlidersHorizontal size={19} />
              <span>Use my pantry</span>
            </button>
          </div>

          {error && (
            <div className="notice" role="status">
              <span>{error}</span>
              <button type="button" onClick={() => setError(null)} aria-label="Dismiss message"><X size={18} /></button>
            </div>
          )}

          {!results && (
            <div className="category-tabs" role="tablist" aria-label="Meal categories">
              {categories.map((item) => (
                <button
                  type="button"
                  role="tab"
                  aria-selected={category === item.value}
                  className={category === item.value ? 'active' : ''}
                  onClick={() => setCategory(item.value)}
                  key={item.value}
                >
                  {item.label}
                </button>
              ))}
            </div>
          )}

          {results && <PantryStrip response={results} />}

          {searching && (
            <div className="search-progress" role="status" aria-live="polite">
              <span /> Finding meals that fit your pantry…
            </div>
          )}

          {loading ? <LoadingMeals /> : (
            <div className={results ? 'result-list' : 'meal-rail'} aria-busy={searching}>
              {displayed.map((recipe, index) => (
                <RecipeCard recipe={recipe} ranked={Boolean(results)} featured={index === 0 && !results} onOpen={openRecipe} key={recipe.slug} />
              ))}
            </div>
          )}

          {!loading && displayed.length === 0 && (
            <div className="empty-state">
              <Utensils size={32} />
              <h2>No grounded matches yet</h2>
              <p>Try another category or allow a little more cooking time. We will not add an unrelated recipe just to fill the list.</p>
              <button className="secondary-button" type="button" onClick={() => setPantryOpen(true)}>Adjust pantry search</button>
            </div>
          )}

          <footer>
            <span>Nutrition is shown only when its source and basis are known.</span>
            <a href="https://theunitools.com/en/data" target="_blank" rel="noreferrer">Public recipe data: UniTools · CC BY-SA 4.0</a>
          </footer>
        </section>
      </main>

      {detail && <RecipeDrawer recipe={detail} pantry={pantry} target={target} exclusions={exclusionList} onClose={closeRecipe} />}
    </div>
  )
}

function PantryStrip({ response }: { response: SearchResponse }) {
  const pantry = response.parsed_pantry
  const deterministicBasics = pantry.basics.filter((term) => pantry.deterministic.includes(term))
  const genericBasics = pantry.basics.filter((term) => !pantry.deterministic.includes(term) && !pantry.refined.includes(term))
  const deterministicCore = pantry.deterministic.filter((term) => !pantry.basics.includes(term))
  const fallbackMessages: Record<string, string> = {
    service_unavailable: 'The local helper is not running. Start Ollama to refine unmatched words; direct matches still work.',
    model_missing: `The ${pantry.model_status.model} model is not installed. Direct ingredient matches still work.`,
    timeout: 'The local helper took too long, so these results use direct ingredient matches.',
    invalid_output: 'The local helper could not safely resolve the remaining words, so they stayed unmatched.',
  }
  return (
    <div className="prep-strip" aria-label="Pantry terms">
      <span className="prep-label">In your pantry</span>
      <div>
        {deterministicCore.map((term) => <span className="ingredient-chip matched" key={term}><Check size={13} />{term}</span>)}
        {deterministicBasics.map((term) => <span className="ingredient-chip basic" key={term}>{term}<small>basic</small></span>)}
        {genericBasics.map((term) => <span className="ingredient-chip basic" key={term}>{term}<small>basic</small></span>)}
        {pantry.refined.map((term) => <span className={`ingredient-chip refined ${pantry.basics.includes(term) ? 'basic' : ''}`} key={term}><Sparkles size={13} />{term}{pantry.basics.includes(term) && <small>basic</small>}</span>)}
        {pantry.unresolved.map((term) => <span className="ingredient-chip unresolved" key={term}>{term}?</span>)}
      </div>
      {pantry.mode === 'locally_refined' && <p className="parse-note"><Sparkles size={14} /> Ambiguous words were understood by Gemma on this device.</p>}
      {pantry.mode === 'deterministic_fallback' && <p className="parse-note fallback">{fallbackMessages[pantry.model_status.reason] || 'The local helper was unavailable, so results use direct ingredient matches.'}</p>}
    </div>
  )
}

function RecipeCard({ recipe, ranked, featured, onOpen }: { recipe: RecipeSummary; ranked: boolean; featured: boolean; onOpen: (slug: string) => void }) {
  return (
    <article className={`recipe-card ${featured ? 'is-featured' : ''}`}>
      <button className="recipe-card-action" type="button" onClick={() => onOpen(recipe.slug)} aria-label={`View ${recipe.name}`}>
        <div className="recipe-image-wrap">
          <RecipeArtwork recipe={recipe} eager={featured} />
          {recipe.country === 'India' && <span className="image-label">Indian</span>}
        </div>
        <div className="recipe-copy">
          <div className="recipe-meta"><span>{recipe.cuisine}</span><span><Clock3 size={14} /> {recipe.total_minutes === null ? 'Time not listed' : `${recipe.total_minutes} min`}</span></div>
          <h2>{recipe.name}</h2>
          <p className="recipe-summary">{recipe.summary}</p>
          {ranked && recipe.reasons && <p className="rank-reason">{recipe.reasons[0]}</p>}
          {ranked && (
            <div className="mini-prep-strip">
              {recipe.available_ingredients?.slice(0, 3).map((term) => <span className="ingredient-chip matched" key={term}>{term}</span>)}
              {recipe.missing_ingredients?.slice(0, 2).map((term) => <span className="ingredient-chip missing" key={term}>{term}</span>)}
            </div>
          )}
          <div className="nutrition-row">
            <span><strong>{recipe.protein_g === null ? '—' : `${recipe.protein_g}g`}</strong> protein</span>
            <span><strong>{recipe.calories === null ? '—' : recipe.calories}</strong> kcal</span>
            <ArrowRight className="open-arrow" size={20} aria-hidden="true" />
          </div>
        </div>
      </button>
    </article>
  )
}

function RecipeArtwork({ recipe, eager }: { recipe: RecipeSummary; eager: boolean }) {
  const [failedUrl, setFailedUrl] = useState<string | null>(null)
  if (!recipe.photo || failedUrl === recipe.photo.url) return <div className="image-fallback"><Utensils size={28} /></div>
  return <img src={recipe.photo.url} alt="" loading={eager ? 'eager' : 'lazy'} onError={() => setFailedUrl(recipe.photo?.url || null)} />
}

function LoadingMeals() {
  return <div className="loading-meals" aria-label="Loading meal ideas">{[1, 2, 3].map((item) => <div className="meal-skeleton" key={item}><span /><div><span /><span /><span /></div></div>)}</div>
}

function RecipeDrawer({ recipe, pantry, target, exclusions, onClose }: {
  recipe: RecipeDetail
  pantry: string
  target: number
  exclusions: string[]
  onClose: () => void
}) {
  const [servings, setServings] = useState<number | ''>(recipe.servings || '')
  const [confirmed, setConfirmed] = useState<ConfirmedNutrition | null>(recipe.servings && recipe.nutrition ? {
    servings: recipe.servings,
    nutrition: recipe.nutrition,
    basis: 'source_per_serving',
    source: recipe.source.attribution,
  } : null)
  const [adaptation, setAdaptation] = useState<AdaptationResult | null>(null)
  const [adaptationError, setAdaptationError] = useState<string | null>(null)
  const [confirming, setConfirming] = useState(false)
  const [adapting, setAdapting] = useState(false)

  async function confirmServings() {
    if (servings === '') return
    setConfirming(true)
    setAdaptationError(null)
    try {
      setConfirmed(await confirmRecipeNutrition(recipe.slug, servings))
    } catch (requestError) {
      setAdaptationError(requestError instanceof Error ? requestError.message : 'Nutrition could not be calculated.')
    } finally {
      setConfirming(false)
    }
  }

  async function requestAdaptation() {
    setAdapting(true)
    setAdaptationError(null)
    try {
      setAdaptation(await adaptRecipe(recipe.slug, {
        pantry,
        protein_target_g: target,
        exclusions,
        servings: servings === '' ? null : servings,
      }))
    } catch (requestError) {
      setAdaptationError(requestError instanceof Error ? requestError.message : 'The local adaptation could not be validated.')
    } finally {
      setAdapting(false)
    }
  }

  return (
    <div className="drawer-backdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <section className="recipe-drawer" role="dialog" aria-modal="true" aria-labelledby="recipe-title">
        <div className="drawer-bar">
          <button className="back-link" type="button" onClick={onClose}><ArrowLeft size={19} /> Back to meals</button>
          <button className="icon-button" type="button" onClick={onClose} aria-label="Close recipe"><X size={21} /></button>
        </div>
        {recipe.photo && <img className="detail-image" src={recipe.photo.url} alt="" />}
        <div className="detail-body">
          <p className="detail-meta">{recipe.cuisine} · {recipe.total_minutes === null ? 'Time not listed' : `${recipe.total_minutes} minutes`} · {recipe.servings === null ? 'Servings not listed' : `${recipe.servings} servings`}</p>
          <h1 id="recipe-title">{recipe.name}</h1>
          <p className="detail-summary">{recipe.summary}</p>
          {recipe.nutrition ? (
            <div className="detail-nutrition">
              <span><strong>{recipe.nutrition.protein}g</strong> protein</span>
              <span><strong>{recipe.nutrition.calories}</strong> kcal</span>
              {recipe.nutrition.carbs !== null && <span><strong>{recipe.nutrition.carbs}g</strong> carbs</span>}
              <span><strong>{recipe.nutrition.fat}g</strong> fat</span>
              {recipe.nutrition_basis === 'per_100g' && <span>per 100g</span>}
            </div>
          ) : <p className="detail-summary">Nutrition not listed in the source dataset.</p>}

          <div className="recipe-columns">
            <section>
              <h2>Ingredients</h2>
              <ul className="ingredient-list">
                {recipe.ingredients.map((ingredient) => (
                  <li key={`${ingredient.id}-${ingredient.quantity}`}>
                    <span>{ingredient.name}{ingredient.note ? <small>{ingredient.note}</small> : null}</span>
                    <strong>{ingredient.quantity ?? ''} {formatUnit(ingredient.unit)}</strong>
                  </li>
                ))}
              </ul>
            </section>
            <section>
              <h2>Method</h2>
              <ol className="steps-list">
                {recipe.steps.map((step, index) => <li key={index}><span>{index + 1}</span><p>{step.text}</p></li>)}
              </ol>
            </section>
          </div>

          <section className="adaptation-panel" aria-labelledby="adaptation-title">
            <div>
              <h2 id="adaptation-title">Make it work with your pantry</h2>
              <p>Gemma can suggest a small, grounded change. Nutrition is recalculated from local USDA records—not generated by the model.</p>
            </div>
            {!pantry.trim() ? (
              <p className="adaptation-message">Add your ingredients in the pantry search before requesting an adaptation.</p>
            ) : (
              <>
                {recipe.servings === null && !confirmed && (
                  <div className="serving-confirmation">
                    <label htmlFor="adaptation-servings">How many servings will this recipe make?</label>
                    <div>
                      <input id="adaptation-servings" type="number" min="1" max="24" value={servings} onChange={(event) => setServings(event.target.value === '' ? '' : Number(event.target.value))} />
                      <button className="secondary-button" type="button" disabled={confirming || servings === ''} onClick={confirmServings}>{confirming ? 'Calculating…' : 'Confirm servings'}</button>
                    </div>
                    <small>We ask because Recipe1M does not provide a reliable serving yield.</small>
                  </div>
                )}
                {confirmed && (
                  <p className="confirmed-nutrition"><Check size={16} /> {confirmed.nutrition.protein}g protein and {confirmed.nutrition.calories} kcal per serving for {confirmed.servings} servings.</p>
                )}
                <button className="primary-button" type="button" disabled={adapting || !confirmed} onClick={requestAdaptation}>
                  {adapting ? 'Validating locally…' : 'Adapt using my pantry'}
                  {!adapting && <Sparkles size={18} />}
                </button>
              </>
            )}
            {adaptationError && <p className="adaptation-error" role="alert">{adaptationError}</p>}
            {adaptation && <AdaptationComparison result={adaptation} target={target} />}
          </section>

          <div className="source-note">
            <p>{recipe.nutrition_basis === 'per_100g' ? 'Nutrition values are source data per 100g.' : recipe.nutrition ? 'Approximate nutrition per serving from the source dataset.' : 'Nutrition is not available for this recipe.'} This is cooking guidance, not medical advice.</p>
            <a href={recipe.source.homepage} target="_blank" rel="noreferrer">{recipe.source.attribution} · {recipe.source.license}</a>
            {recipe.photo && <span>Photo: {recipe.photo.author} · {recipe.photo.license}</span>}
          </div>
        </div>
      </section>
    </div>
  )
}

function AdaptationComparison({ result, target }: { result: AdaptationResult; target: number }) {
  return (
    <div className="adaptation-result">
      <h3>{result.title}</h3>
      <div className="nutrition-comparison">
        <div><small>Original</small><strong>{result.original_nutrition.protein}g</strong><span>protein</span><strong>{result.original_nutrition.calories}</strong><span>kcal</span></div>
        <ArrowRight size={20} />
        <div><small>Adapted</small><strong>{result.adapted_nutrition.protein}g</strong><span>protein</span><strong>{result.adapted_nutrition.calories}</strong><span>kcal</span></div>
      </div>
      <p className="target-note">Target: {target}g · {Math.abs(result.protein_difference_g)}g {result.protein_difference_g >= 0 ? 'above' : 'below'} target</p>
      <h4>Validated changes</h4>
      <ul className="adaptation-changes">
        {result.changes.map((change) => <li key={change.ingredient_id}><strong>{change.action === 'add' ? 'Add' : 'Increase'} {change.name} by {change.quantity_g}g</strong><span>{change.reason}</span></li>)}
      </ul>
      {result.instruction_notes.length > 0 && <><h4>Method notes</h4><ul className="adaptation-notes">{result.instruction_notes.map((note) => <li key={note}>{note}</li>)}</ul></>}
      <p className="adaptation-provenance">Nutrition calculated from {result.nutrition_source.name} ({result.nutrition_source.basis}). Approximate cooking guidance only.</p>
    </div>
  )
}

function formatUnit(unit: string) {
  const units: Record<string, string> = { piece: '', toTaste: 'to taste', tbsp: 'tbsp', tsp: 'tsp' }
  return units[unit] ?? unit
}

export default App
