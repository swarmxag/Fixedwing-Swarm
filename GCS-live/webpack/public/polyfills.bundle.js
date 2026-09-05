/*
 * ATTENTION: The "eval" devtool has been used (maybe by default in mode: "development").
 * This devtool is neither made for production nor for readable output files.
 * It uses "eval()" calls to create a separate source file in the browser devtools.
 * If you are trying to read the output file, select a different devtool (https://webpack.js.org/configuration/devtool/)
 * or disable the default devtool with "devtool: false".
 * If you are looking for production-ready output files, see mode: "production" (https://webpack.js.org/configuration/mode/).
 */
/******/ (() => { // webpackBootstrap
/******/ 	"use strict";
/******/ 	var __webpack_modules__ = ({

/***/ "./node_modules/core-js/actual/structured-clone.js"
/*!*********************************************************!*\
  !*** ./node_modules/core-js/actual/structured-clone.js ***!
  \*********************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar parent = __webpack_require__(/*! ../stable/structured-clone */ \"./node_modules/core-js/stable/structured-clone.js\");\n\nmodule.exports = parent;\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/actual/structured-clone.js?\n}");

/***/ },

/***/ "./node_modules/core-js/full/set/add-all.js"
/*!**************************************************!*\
  !*** ./node_modules/core-js/full/set/add-all.js ***!
  \**************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\n__webpack_require__(/*! ../../modules/es.set */ \"./node_modules/core-js/modules/es.set.js\");\n__webpack_require__(/*! ../../modules/esnext.set.add-all */ \"./node_modules/core-js/modules/esnext.set.add-all.js\");\nvar entryUnbind = __webpack_require__(/*! ../../internals/entry-unbind */ \"./node_modules/core-js/internals/entry-unbind.js\");\n\nmodule.exports = entryUnbind('Set', 'addAll');\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/full/set/add-all.js?\n}");

/***/ },

/***/ "./node_modules/core-js/full/set/delete-all.js"
/*!*****************************************************!*\
  !*** ./node_modules/core-js/full/set/delete-all.js ***!
  \*****************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\n__webpack_require__(/*! ../../modules/es.set */ \"./node_modules/core-js/modules/es.set.js\");\n__webpack_require__(/*! ../../modules/esnext.set.delete-all */ \"./node_modules/core-js/modules/esnext.set.delete-all.js\");\nvar entryUnbind = __webpack_require__(/*! ../../internals/entry-unbind */ \"./node_modules/core-js/internals/entry-unbind.js\");\n\nmodule.exports = entryUnbind('Set', 'deleteAll');\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/full/set/delete-all.js?\n}");

/***/ },

/***/ "./node_modules/core-js/full/structured-clone.js"
/*!*******************************************************!*\
  !*** ./node_modules/core-js/full/structured-clone.js ***!
  \*******************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar parent = __webpack_require__(/*! ../actual/structured-clone */ \"./node_modules/core-js/actual/structured-clone.js\");\n\nmodule.exports = parent;\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/full/structured-clone.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/a-callable.js"
/*!******************************************************!*\
  !*** ./node_modules/core-js/internals/a-callable.js ***!
  \******************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar isCallable = __webpack_require__(/*! ../internals/is-callable */ \"./node_modules/core-js/internals/is-callable.js\");\nvar tryToString = __webpack_require__(/*! ../internals/try-to-string */ \"./node_modules/core-js/internals/try-to-string.js\");\n\nvar $TypeError = TypeError;\n\n// `Assert: IsCallable(argument) is true`\nmodule.exports = function (argument) {\n  if (isCallable(argument)) return argument;\n  throw new $TypeError(tryToString(argument) + ' is not a function');\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/a-callable.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/a-possible-prototype.js"
/*!****************************************************************!*\
  !*** ./node_modules/core-js/internals/a-possible-prototype.js ***!
  \****************************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar isPossiblePrototype = __webpack_require__(/*! ../internals/is-possible-prototype */ \"./node_modules/core-js/internals/is-possible-prototype.js\");\n\nvar $String = String;\nvar $TypeError = TypeError;\n\nmodule.exports = function (argument) {\n  if (isPossiblePrototype(argument)) return argument;\n  throw new $TypeError(\"Can't set \" + $String(argument) + ' as a prototype');\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/a-possible-prototype.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/a-set.js"
/*!*************************************************!*\
  !*** ./node_modules/core-js/internals/a-set.js ***!
  \*************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar has = (__webpack_require__(/*! ../internals/set-helpers */ \"./node_modules/core-js/internals/set-helpers.js\").has);\n\n// Perform ? RequireInternalSlot(M, [[SetData]])\nmodule.exports = function (it) {\n  has(it);\n  return it;\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/a-set.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/add-to-unscopables.js"
/*!**************************************************************!*\
  !*** ./node_modules/core-js/internals/add-to-unscopables.js ***!
  \**************************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar wellKnownSymbol = __webpack_require__(/*! ../internals/well-known-symbol */ \"./node_modules/core-js/internals/well-known-symbol.js\");\nvar create = __webpack_require__(/*! ../internals/object-create */ \"./node_modules/core-js/internals/object-create.js\");\nvar defineProperty = (__webpack_require__(/*! ../internals/object-define-property */ \"./node_modules/core-js/internals/object-define-property.js\").f);\n\nvar UNSCOPABLES = wellKnownSymbol('unscopables');\nvar ArrayPrototype = Array.prototype;\n\n// Array.prototype[@@unscopables]\n// https://tc39.es/ecma262/#sec-array.prototype-@@unscopables\nif (ArrayPrototype[UNSCOPABLES] === undefined) {\n  defineProperty(ArrayPrototype, UNSCOPABLES, {\n    configurable: true,\n    value: create(null)\n  });\n}\n\n// add a key to Array.prototype[@@unscopables]\nmodule.exports = function (key) {\n  ArrayPrototype[UNSCOPABLES][key] = true;\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/add-to-unscopables.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/an-instance.js"
/*!*******************************************************!*\
  !*** ./node_modules/core-js/internals/an-instance.js ***!
  \*******************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar isPrototypeOf = __webpack_require__(/*! ../internals/object-is-prototype-of */ \"./node_modules/core-js/internals/object-is-prototype-of.js\");\n\nvar $TypeError = TypeError;\n\nmodule.exports = function (it, Prototype) {\n  if (isPrototypeOf(Prototype, it)) return it;\n  throw new $TypeError('Incorrect invocation');\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/an-instance.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/an-object.js"
/*!*****************************************************!*\
  !*** ./node_modules/core-js/internals/an-object.js ***!
  \*****************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar isObject = __webpack_require__(/*! ../internals/is-object */ \"./node_modules/core-js/internals/is-object.js\");\n\nvar $String = String;\nvar $TypeError = TypeError;\n\n// `Assert: Type(argument) is Object`\nmodule.exports = function (argument) {\n  if (isObject(argument)) return argument;\n  throw new $TypeError($String(argument) + ' is not an object');\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/an-object.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/array-buffer-non-extensible.js"
/*!***********************************************************************!*\
  !*** ./node_modules/core-js/internals/array-buffer-non-extensible.js ***!
  \***********************************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\n// FF26- bug: ArrayBuffers are non-extensible, but Object.isExtensible does not report it\nvar fails = __webpack_require__(/*! ../internals/fails */ \"./node_modules/core-js/internals/fails.js\");\n\nmodule.exports = fails(function () {\n  if (typeof ArrayBuffer == 'function') {\n    var buffer = new ArrayBuffer(8);\n    // eslint-disable-next-line es/no-object-isextensible, es/no-object-defineproperty -- safe\n    if (Object.isExtensible(buffer)) Object.defineProperty(buffer, 'a', { value: 8 });\n  }\n});\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/array-buffer-non-extensible.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/array-includes.js"
/*!**********************************************************!*\
  !*** ./node_modules/core-js/internals/array-includes.js ***!
  \**********************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar toIndexedObject = __webpack_require__(/*! ../internals/to-indexed-object */ \"./node_modules/core-js/internals/to-indexed-object.js\");\nvar toAbsoluteIndex = __webpack_require__(/*! ../internals/to-absolute-index */ \"./node_modules/core-js/internals/to-absolute-index.js\");\nvar lengthOfArrayLike = __webpack_require__(/*! ../internals/length-of-array-like */ \"./node_modules/core-js/internals/length-of-array-like.js\");\n\n// `Array.prototype.{ indexOf, includes }` methods implementation\nvar createMethod = function (IS_INCLUDES) {\n  return function ($this, el, fromIndex) {\n    var O = toIndexedObject($this);\n    var length = lengthOfArrayLike(O);\n    if (length === 0) return !IS_INCLUDES && -1;\n    var index = toAbsoluteIndex(fromIndex, length);\n    var value;\n    // Array#includes uses SameValueZero equality algorithm\n    // eslint-disable-next-line no-self-compare -- NaN check\n    if (IS_INCLUDES && el !== el) while (length > index) {\n      value = O[index++];\n      // eslint-disable-next-line no-self-compare -- NaN check\n      if (value !== value) return true;\n    // Array#indexOf ignores holes, Array#includes - not\n    } else for (;length > index; index++) {\n      if ((IS_INCLUDES || index in O) && O[index] === el) return IS_INCLUDES || index || 0;\n    } return !IS_INCLUDES && -1;\n  };\n};\n\nmodule.exports = {\n  // `Array.prototype.includes` method\n  // https://tc39.es/ecma262/#sec-array.prototype.includes\n  includes: createMethod(true),\n  // `Array.prototype.indexOf` method\n  // https://tc39.es/ecma262/#sec-array.prototype.indexof\n  indexOf: createMethod(false)\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/array-includes.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/array-slice.js"
/*!*******************************************************!*\
  !*** ./node_modules/core-js/internals/array-slice.js ***!
  \*******************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar uncurryThis = __webpack_require__(/*! ../internals/function-uncurry-this */ \"./node_modules/core-js/internals/function-uncurry-this.js\");\n\nmodule.exports = uncurryThis([].slice);\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/array-slice.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/check-correctness-of-iteration.js"
/*!**************************************************************************!*\
  !*** ./node_modules/core-js/internals/check-correctness-of-iteration.js ***!
  \**************************************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar wellKnownSymbol = __webpack_require__(/*! ../internals/well-known-symbol */ \"./node_modules/core-js/internals/well-known-symbol.js\");\n\nvar ITERATOR = wellKnownSymbol('iterator');\nvar SAFE_CLOSING = false;\n\ntry {\n  var called = 0;\n  var iteratorWithReturn = {\n    next: function () {\n      return { done: !!called++ };\n    },\n    'return': function () {\n      SAFE_CLOSING = true;\n    }\n  };\n  // eslint-disable-next-line unicorn/no-immediate-mutation -- ES3 syntax limitation\n  iteratorWithReturn[ITERATOR] = function () {\n    return this;\n  };\n  // eslint-disable-next-line es/no-array-from, no-throw-literal -- required for testing\n  Array.from(iteratorWithReturn, function () { throw 2; });\n} catch (error) { /* empty */ }\n\nmodule.exports = function (exec, SKip_CLOSING) {\n  try {\n    if (!SKip_CLOSING && !SAFE_CLOSING) return false;\n  } catch (error) { return false; } // workaround of old WebKit + `eval` bug\n  var ITERATION_SUPPORT = false;\n  try {\n    var object = {};\n    // eslint-disable-next-line unicorn/no-immediate-mutation -- ES3 syntax limitation\n    object[ITERATOR] = function () {\n      return {\n        next: function () {\n          return { done: ITERATION_SUPPORT = true };\n        }\n      };\n    };\n    exec(object);\n  } catch (error) { /* empty */ }\n  return ITERATION_SUPPORT;\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/check-correctness-of-iteration.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/classof-raw.js"
/*!*******************************************************!*\
  !*** ./node_modules/core-js/internals/classof-raw.js ***!
  \*******************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar uncurryThis = __webpack_require__(/*! ../internals/function-uncurry-this */ \"./node_modules/core-js/internals/function-uncurry-this.js\");\n\nvar toString = uncurryThis({}.toString);\nvar stringSlice = uncurryThis(''.slice);\n\nmodule.exports = function (it) {\n  return stringSlice(toString(it), 8, -1);\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/classof-raw.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/classof.js"
/*!***************************************************!*\
  !*** ./node_modules/core-js/internals/classof.js ***!
  \***************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar TO_STRING_TAG_SUPPORT = __webpack_require__(/*! ../internals/to-string-tag-support */ \"./node_modules/core-js/internals/to-string-tag-support.js\");\nvar isCallable = __webpack_require__(/*! ../internals/is-callable */ \"./node_modules/core-js/internals/is-callable.js\");\nvar classofRaw = __webpack_require__(/*! ../internals/classof-raw */ \"./node_modules/core-js/internals/classof-raw.js\");\nvar wellKnownSymbol = __webpack_require__(/*! ../internals/well-known-symbol */ \"./node_modules/core-js/internals/well-known-symbol.js\");\n\nvar TO_STRING_TAG = wellKnownSymbol('toStringTag');\nvar $Object = Object;\n\n// ES3 wrong here\nvar CORRECT_ARGUMENTS = classofRaw(function () { return arguments; }()) === 'Arguments';\n\n// fallback for IE11 Script Access Denied error\nvar tryGet = function (it, key) {\n  try {\n    return it[key];\n  } catch (error) { /* empty */ }\n};\n\n// getting tag from ES6+ `Object.prototype.toString`\nmodule.exports = TO_STRING_TAG_SUPPORT ? classofRaw : function (it) {\n  var O, tag, result;\n  return it === undefined ? 'Undefined' : it === null ? 'Null'\n    // @@toStringTag case\n    : typeof (tag = tryGet(O = $Object(it), TO_STRING_TAG)) == 'string' ? tag\n    // builtinTag case\n    : CORRECT_ARGUMENTS ? classofRaw(O)\n    // ES3 arguments fallback\n    : (result = classofRaw(O)) === 'Object' && isCallable(O.callee) ? 'Arguments' : result;\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/classof.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/collection-strong.js"
/*!*************************************************************!*\
  !*** ./node_modules/core-js/internals/collection-strong.js ***!
  \*************************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar create = __webpack_require__(/*! ../internals/object-create */ \"./node_modules/core-js/internals/object-create.js\");\nvar defineBuiltInAccessor = __webpack_require__(/*! ../internals/define-built-in-accessor */ \"./node_modules/core-js/internals/define-built-in-accessor.js\");\nvar defineBuiltIns = __webpack_require__(/*! ../internals/define-built-ins */ \"./node_modules/core-js/internals/define-built-ins.js\");\nvar bind = __webpack_require__(/*! ../internals/function-bind-context */ \"./node_modules/core-js/internals/function-bind-context.js\");\nvar anInstance = __webpack_require__(/*! ../internals/an-instance */ \"./node_modules/core-js/internals/an-instance.js\");\nvar isNullOrUndefined = __webpack_require__(/*! ../internals/is-null-or-undefined */ \"./node_modules/core-js/internals/is-null-or-undefined.js\");\nvar iterate = __webpack_require__(/*! ../internals/iterate */ \"./node_modules/core-js/internals/iterate.js\");\nvar defineIterator = __webpack_require__(/*! ../internals/iterator-define */ \"./node_modules/core-js/internals/iterator-define.js\");\nvar createIterResultObject = __webpack_require__(/*! ../internals/create-iter-result-object */ \"./node_modules/core-js/internals/create-iter-result-object.js\");\nvar setSpecies = __webpack_require__(/*! ../internals/set-species */ \"./node_modules/core-js/internals/set-species.js\");\nvar DESCRipTORS = __webpack_require__(/*! ../internals/descriptors */ \"./node_modules/core-js/internals/descriptors.js\");\nvar fastKey = (__webpack_require__(/*! ../internals/internal-metadata */ \"./node_modules/core-js/internals/internal-metadata.js\").fastKey);\nvar InternalStateModule = __webpack_require__(/*! ../internals/internal-state */ \"./node_modules/core-js/internals/internal-state.js\");\n\nvar setInternalState = InternalStateModule.set;\nvar internalStateGetterFor = InternalStateModule.getterFor;\n\nmodule.exports = {\n  getConstructor: function (wrapper, CONSTRUCTOR_NAME, IS_MAP, ADDER) {\n    var Constructor = wrapper(function (that, iterable) {\n      anInstance(that, Prototype);\n      setInternalState(that, {\n        type: CONSTRUCTOR_NAME,\n        index: create(null),\n        first: null,\n        last: null,\n        size: 0\n      });\n      if (!DESCRipTORS) that.size = 0;\n      if (!isNullOrUndefined(iterable)) iterate(iterable, that[ADDER], { that: that, AS_ENTRIES: IS_MAP });\n    });\n\n    var Prototype = Constructor.prototype;\n\n    var getInternalState = internalStateGetterFor(CONSTRUCTOR_NAME);\n\n    var define = function (that, key, value) {\n      var state = getInternalState(that);\n      var entry = getEntry(that, key);\n      var previous, index;\n      // change existing entry\n      if (entry) {\n        entry.value = value;\n      // create new entry\n      } else {\n        state.last = entry = {\n          index: index = fastKey(key, true),\n          key: key,\n          value: value,\n          previous: previous = state.last,\n          next: null,\n          removed: false\n        };\n        if (!state.first) state.first = entry;\n        if (previous) previous.next = entry;\n        if (DESCRipTORS) state.size++;\n        else that.size++;\n        // add to index\n        if (index !== 'F') state.index[index] = entry;\n      } return that;\n    };\n\n    var getEntry = function (that, key) {\n      var state = getInternalState(that);\n      // fast case\n      var index = fastKey(key);\n      var entry;\n      if (index !== 'F') return state.index[index];\n      // frozen object case\n      for (entry = state.first; entry; entry = entry.next) {\n        if (entry.key === key) return entry;\n      }\n    };\n\n    defineBuiltIns(Prototype, {\n      // `{ Map, Set }.prototype.clear()` methods\n      // https://tc39.es/ecma262/#sec-map.prototype.clear\n      // https://tc39.es/ecma262/#sec-set.prototype.clear\n      clear: function clear() {\n        var that = this;\n        var state = getInternalState(that);\n        var entry = state.first;\n        while (entry) {\n          entry.removed = true;\n          if (entry.previous) entry.previous = entry.previous.next = null;\n          entry = entry.next;\n        }\n        state.first = state.last = null;\n        state.index = create(null);\n        if (DESCRipTORS) state.size = 0;\n        else that.size = 0;\n      },\n      // `{ Map, Set }.prototype.delete(key)` methods\n      // https://tc39.es/ecma262/#sec-map.prototype.delete\n      // https://tc39.es/ecma262/#sec-set.prototype.delete\n      'delete': function (key) {\n        var that = this;\n        var state = getInternalState(that);\n        var entry = getEntry(that, key);\n        if (entry) {\n          var next = entry.next;\n          var prev = entry.previous;\n          delete state.index[entry.index];\n          entry.removed = true;\n          if (prev) prev.next = next;\n          if (next) next.previous = prev;\n          if (state.first === entry) state.first = next;\n          if (state.last === entry) state.last = prev;\n          if (DESCRipTORS) state.size--;\n          else that.size--;\n        } return !!entry;\n      },\n      // `{ Map, Set }.prototype.forEach(callbackfn, thisArg = undefined)` methods\n      // https://tc39.es/ecma262/#sec-map.prototype.foreach\n      // https://tc39.es/ecma262/#sec-set.prototype.foreach\n      forEach: function forEach(callbackfn /* , that = undefined */) {\n        var state = getInternalState(this);\n        var boundFunction = bind(callbackfn, arguments.length > 1 ? arguments[1] : undefined);\n        var entry;\n        while (entry = entry ? entry.next : state.first) {\n          boundFunction(entry.value, entry.key, this);\n          // revert to the last existing entry\n          while (entry && entry.removed) entry = entry.previous;\n        }\n      },\n      // `{ Map, Set}.prototype.has(key)` methods\n      // https://tc39.es/ecma262/#sec-map.prototype.has\n      // https://tc39.es/ecma262/#sec-set.prototype.has\n      has: function has(key) {\n        return !!getEntry(this, key);\n      }\n    });\n\n    defineBuiltIns(Prototype, IS_MAP ? {\n      // `Map.prototype.get(key)` method\n      // https://tc39.es/ecma262/#sec-map.prototype.get\n      get: function get(key) {\n        var entry = getEntry(this, key);\n        return entry && entry.value;\n      },\n      // `Map.prototype.set(key, value)` method\n      // https://tc39.es/ecma262/#sec-map.prototype.set\n      set: function set(key, value) {\n        return define(this, key === 0 ? 0 : key, value);\n      }\n    } : {\n      // `Set.prototype.add(value)` method\n      // https://tc39.es/ecma262/#sec-set.prototype.add\n      add: function add(value) {\n        return define(this, value = value === 0 ? 0 : value, value);\n      }\n    });\n    if (DESCRipTORS) defineBuiltInAccessor(Prototype, 'size', {\n      configurable: true,\n      get: function () {\n        return getInternalState(this).size;\n      }\n    });\n    return Constructor;\n  },\n  setStrong: function (Constructor, CONSTRUCTOR_NAME, IS_MAP) {\n    var ITERATOR_NAME = CONSTRUCTOR_NAME + ' Iterator';\n    var getInternalCollectionState = internalStateGetterFor(CONSTRUCTOR_NAME);\n    var getInternalIteratorState = internalStateGetterFor(ITERATOR_NAME);\n    // `{ Map, Set }.prototype.{ keys, values, entries, @@iterator }()` methods\n    // https://tc39.es/ecma262/#sec-map.prototype.entries\n    // https://tc39.es/ecma262/#sec-map.prototype.keys\n    // https://tc39.es/ecma262/#sec-map.prototype.values\n    // https://tc39.es/ecma262/#sec-map.prototype-@@iterator\n    // https://tc39.es/ecma262/#sec-set.prototype.entries\n    // https://tc39.es/ecma262/#sec-set.prototype.keys\n    // https://tc39.es/ecma262/#sec-set.prototype.values\n    // https://tc39.es/ecma262/#sec-set.prototype-@@iterator\n    defineIterator(Constructor, CONSTRUCTOR_NAME, function (iterated, kind) {\n      setInternalState(this, {\n        type: ITERATOR_NAME,\n        target: iterated,\n        state: getInternalCollectionState(iterated),\n        kind: kind,\n        last: null\n      });\n    }, function () {\n      var state = getInternalIteratorState(this);\n      var kind = state.kind;\n      var entry = state.last;\n      // revert to the last existing entry\n      while (entry && entry.removed) entry = entry.previous;\n      // get next entry\n      if (!state.target || !(state.last = entry = entry ? entry.next : state.state.first)) {\n        // or finish the iteration\n        state.target = null;\n        return createIterResultObject(undefined, true);\n      }\n      // return step by kind\n      if (kind === 'keys') return createIterResultObject(entry.key, false);\n      if (kind === 'values') return createIterResultObject(entry.value, false);\n      return createIterResultObject([entry.key, entry.value], false);\n    }, IS_MAP ? 'entries' : 'values', !IS_MAP, true);\n\n    // `{ Map, Set }.prototype[@@species]` accessors\n    // https://tc39.es/ecma262/#sec-get-map-@@species\n    // https://tc39.es/ecma262/#sec-get-set-@@species\n    setSpecies(CONSTRUCTOR_NAME);\n  }\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/collection-strong.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/collection.js"
/*!******************************************************!*\
  !*** ./node_modules/core-js/internals/collection.js ***!
  \******************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar $ = __webpack_require__(/*! ../internals/export */ \"./node_modules/core-js/internals/export.js\");\nvar globalThis = __webpack_require__(/*! ../internals/global-this */ \"./node_modules/core-js/internals/global-this.js\");\nvar uncurryThis = __webpack_require__(/*! ../internals/function-uncurry-this */ \"./node_modules/core-js/internals/function-uncurry-this.js\");\nvar isForced = __webpack_require__(/*! ../internals/is-forced */ \"./node_modules/core-js/internals/is-forced.js\");\nvar defineBuiltIn = __webpack_require__(/*! ../internals/define-built-in */ \"./node_modules/core-js/internals/define-built-in.js\");\nvar InternalMetadataModule = __webpack_require__(/*! ../internals/internal-metadata */ \"./node_modules/core-js/internals/internal-metadata.js\");\nvar iterate = __webpack_require__(/*! ../internals/iterate */ \"./node_modules/core-js/internals/iterate.js\");\nvar anInstance = __webpack_require__(/*! ../internals/an-instance */ \"./node_modules/core-js/internals/an-instance.js\");\nvar isCallable = __webpack_require__(/*! ../internals/is-callable */ \"./node_modules/core-js/internals/is-callable.js\");\nvar isNullOrUndefined = __webpack_require__(/*! ../internals/is-null-or-undefined */ \"./node_modules/core-js/internals/is-null-or-undefined.js\");\nvar isObject = __webpack_require__(/*! ../internals/is-object */ \"./node_modules/core-js/internals/is-object.js\");\nvar fails = __webpack_require__(/*! ../internals/fails */ \"./node_modules/core-js/internals/fails.js\");\nvar checkCorrectnessOfIteration = __webpack_require__(/*! ../internals/check-correctness-of-iteration */ \"./node_modules/core-js/internals/check-correctness-of-iteration.js\");\nvar setToStringTag = __webpack_require__(/*! ../internals/set-to-string-tag */ \"./node_modules/core-js/internals/set-to-string-tag.js\");\nvar inheritIfRequired = __webpack_require__(/*! ../internals/inherit-if-required */ \"./node_modules/core-js/internals/inherit-if-required.js\");\n\nmodule.exports = function (CONSTRUCTOR_NAME, wrapper, common) {\n  var IS_MAP = CONSTRUCTOR_NAME.indexOf('Map') !== -1;\n  var IS_WEAK = CONSTRUCTOR_NAME.indexOf('Weak') !== -1;\n  var ADDER = IS_MAP ? 'set' : 'add';\n  var NativeConstructor = globalThis[CONSTRUCTOR_NAME];\n  var NativePrototype = NativeConstructor && NativeConstructor.prototype;\n  var Constructor = NativeConstructor;\n  var exported = {};\n\n  var fixMethod = function (KEY) {\n    var uncurriedNativeMethod = uncurryThis(NativePrototype[KEY]);\n    defineBuiltIn(NativePrototype, KEY,\n      KEY === 'add' ? function add(value) {\n        uncurriedNativeMethod(this, value === 0 ? 0 : value);\n        return this;\n      } : KEY === 'delete' ? function (key) {\n        return IS_WEAK && !isObject(key) ? false : uncurriedNativeMethod(this, key === 0 ? 0 : key);\n      } : KEY === 'get' ? function get(key) {\n        return IS_WEAK && !isObject(key) ? undefined : uncurriedNativeMethod(this, key === 0 ? 0 : key);\n      } : KEY === 'has' ? function has(key) {\n        return IS_WEAK && !isObject(key) ? false : uncurriedNativeMethod(this, key === 0 ? 0 : key);\n      } : function set(key, value) {\n        uncurriedNativeMethod(this, key === 0 ? 0 : key, value);\n        return this;\n      }\n    );\n  };\n\n  var REPLACE = isForced(\n    CONSTRUCTOR_NAME,\n    !isCallable(NativeConstructor) || !(IS_WEAK || NativePrototype.forEach && !fails(function () {\n      new NativeConstructor().entries().next();\n    }))\n  );\n\n  if (REPLACE) {\n    // create collection constructor\n    Constructor = common.getConstructor(wrapper, CONSTRUCTOR_NAME, IS_MAP, ADDER);\n    InternalMetadataModule.enable();\n  } else if (isForced(CONSTRUCTOR_NAME, true)) {\n    var instance = new Constructor();\n    // early implementations not supports chaining\n    var HASNT_CHAINING = instance[ADDER](IS_WEAK ? {} : -0, 1) !== instance;\n    // V8 ~ Chromium 40- weak-collections throws on primitives, but should return false\n    var THROWS_ON_PRIMITIVES = fails(function () { instance.has(1); });\n    // most early implementations doesn't supports iterables, most modern - not close it correctly\n    // eslint-disable-next-line no-new -- required for testing\n    var ACCEPT_ITERABLES = checkCorrectnessOfIteration(function (iterable) { new NativeConstructor(iterable); });\n    // for early implementations -0 and +0 not the same\n    var BUGGY_ZERO = !IS_WEAK && fails(function () {\n      // V8 ~ Chromium 42- fails only with 5+ elements\n      var $instance = new NativeConstructor();\n      var index = 5;\n      while (index--) $instance[ADDER](index, index);\n      return !$instance.has(-0);\n    });\n\n    if (!ACCEPT_ITERABLES) {\n      Constructor = wrapper(function (dummy, iterable) {\n        anInstance(dummy, NativePrototype);\n        var that = inheritIfRequired(new NativeConstructor(), dummy, Constructor);\n        if (!isNullOrUndefined(iterable)) iterate(iterable, that[ADDER], { that: that, AS_ENTRIES: IS_MAP });\n        return that;\n      });\n      Constructor.prototype = NativePrototype;\n      NativePrototype.constructor = Constructor;\n    }\n\n    if (THROWS_ON_PRIMITIVES || BUGGY_ZERO) {\n      fixMethod('delete');\n      fixMethod('has');\n      IS_MAP && fixMethod('get');\n    }\n\n    if (BUGGY_ZERO || HASNT_CHAINING) fixMethod(ADDER);\n\n    // weak collections should not contains .clear method\n    if (IS_WEAK && NativePrototype.clear) delete NativePrototype.clear;\n  }\n\n  exported[CONSTRUCTOR_NAME] = Constructor;\n  $({ global: true, constructor: true, forced: Constructor !== NativeConstructor }, exported);\n\n  setToStringTag(Constructor, CONSTRUCTOR_NAME);\n\n  if (!IS_WEAK) common.setStrong(Constructor, CONSTRUCTOR_NAME, IS_MAP);\n\n  return Constructor;\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/collection.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/copy-constructor-properties.js"
/*!***********************************************************************!*\
  !*** ./node_modules/core-js/internals/copy-constructor-properties.js ***!
  \***********************************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar hasOwn = __webpack_require__(/*! ../internals/has-own-property */ \"./node_modules/core-js/internals/has-own-property.js\");\nvar ownKeys = __webpack_require__(/*! ../internals/own-keys */ \"./node_modules/core-js/internals/own-keys.js\");\nvar getOwnPropertyDescriptorModule = __webpack_require__(/*! ../internals/object-get-own-property-descriptor */ \"./node_modules/core-js/internals/object-get-own-property-descriptor.js\");\nvar definePropertyModule = __webpack_require__(/*! ../internals/object-define-property */ \"./node_modules/core-js/internals/object-define-property.js\");\n\nmodule.exports = function (target, source, exceptions) {\n  var keys = ownKeys(source);\n  var defineProperty = definePropertyModule.f;\n  var getOwnPropertyDescriptor = getOwnPropertyDescriptorModule.f;\n  for (var i = 0; i < keys.length; i++) {\n    var key = keys[i];\n    if (!hasOwn(target, key) && !(exceptions && hasOwn(exceptions, key))) {\n      defineProperty(target, key, getOwnPropertyDescriptor(source, key));\n    }\n  }\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/copy-constructor-properties.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/correct-prototype-getter.js"
/*!********************************************************************!*\
  !*** ./node_modules/core-js/internals/correct-prototype-getter.js ***!
  \********************************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar fails = __webpack_require__(/*! ../internals/fails */ \"./node_modules/core-js/internals/fails.js\");\n\nmodule.exports = !fails(function () {\n  function F() { /* empty */ }\n  F.prototype.constructor = null;\n  // eslint-disable-next-line es/no-object-getprototypeof -- required for testing\n  return Object.getPrototypeOf(new F()) !== F.prototype;\n});\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/correct-prototype-getter.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/create-iter-result-object.js"
/*!*********************************************************************!*\
  !*** ./node_modules/core-js/internals/create-iter-result-object.js ***!
  \*********************************************************************/
(module) {

eval("{\n// `CreateIterResultObject` abstract operation\n// https://tc39.es/ecma262/#sec-createiterresultobject\nmodule.exports = function (value, done) {\n  return { value: value, done: done };\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/create-iter-result-object.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/create-non-enumerable-property.js"
/*!**************************************************************************!*\
  !*** ./node_modules/core-js/internals/create-non-enumerable-property.js ***!
  \**************************************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar DESCRipTORS = __webpack_require__(/*! ../internals/descriptors */ \"./node_modules/core-js/internals/descriptors.js\");\nvar definePropertyModule = __webpack_require__(/*! ../internals/object-define-property */ \"./node_modules/core-js/internals/object-define-property.js\");\nvar createPropertyDescriptor = __webpack_require__(/*! ../internals/create-property-descriptor */ \"./node_modules/core-js/internals/create-property-descriptor.js\");\n\nmodule.exports = DESCRipTORS ? function (object, key, value) {\n  return definePropertyModule.f(object, key, createPropertyDescriptor(1, value));\n} : function (object, key, value) {\n  object[key] = value;\n  return object;\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/create-non-enumerable-property.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/create-property-descriptor.js"
/*!**********************************************************************!*\
  !*** ./node_modules/core-js/internals/create-property-descriptor.js ***!
  \**********************************************************************/
(module) {

eval("{\nmodule.exports = function (bitmap, value) {\n  return {\n    enumerable: !(bitmap & 1),\n    configurable: !(bitmap & 2),\n    writable: !(bitmap & 4),\n    value: value\n  };\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/create-property-descriptor.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/create-property.js"
/*!***********************************************************!*\
  !*** ./node_modules/core-js/internals/create-property.js ***!
  \***********************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar DESCRipTORS = __webpack_require__(/*! ../internals/descriptors */ \"./node_modules/core-js/internals/descriptors.js\");\nvar definePropertyModule = __webpack_require__(/*! ../internals/object-define-property */ \"./node_modules/core-js/internals/object-define-property.js\");\nvar createPropertyDescriptor = __webpack_require__(/*! ../internals/create-property-descriptor */ \"./node_modules/core-js/internals/create-property-descriptor.js\");\n\nmodule.exports = function (object, key, value) {\n  if (DESCRipTORS) definePropertyModule.f(object, key, createPropertyDescriptor(0, value));\n  else object[key] = value;\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/create-property.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/define-built-in-accessor.js"
/*!********************************************************************!*\
  !*** ./node_modules/core-js/internals/define-built-in-accessor.js ***!
  \********************************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar makeBuiltIn = __webpack_require__(/*! ../internals/make-built-in */ \"./node_modules/core-js/internals/make-built-in.js\");\nvar defineProperty = __webpack_require__(/*! ../internals/object-define-property */ \"./node_modules/core-js/internals/object-define-property.js\");\n\nmodule.exports = function (target, name, descriptor) {\n  if (descriptor.get) makeBuiltIn(descriptor.get, name, { getter: true });\n  if (descriptor.set) makeBuiltIn(descriptor.set, name, { setter: true });\n  return defineProperty.f(target, name, descriptor);\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/define-built-in-accessor.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/define-built-in.js"
/*!***********************************************************!*\
  !*** ./node_modules/core-js/internals/define-built-in.js ***!
  \***********************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar isCallable = __webpack_require__(/*! ../internals/is-callable */ \"./node_modules/core-js/internals/is-callable.js\");\nvar definePropertyModule = __webpack_require__(/*! ../internals/object-define-property */ \"./node_modules/core-js/internals/object-define-property.js\");\nvar makeBuiltIn = __webpack_require__(/*! ../internals/make-built-in */ \"./node_modules/core-js/internals/make-built-in.js\");\nvar defineGlobalProperty = __webpack_require__(/*! ../internals/define-global-property */ \"./node_modules/core-js/internals/define-global-property.js\");\n\nmodule.exports = function (O, key, value, options) {\n  if (!options) options = {};\n  var simple = options.enumerable;\n  var name = options.name !== undefined ? options.name : key;\n  if (isCallable(value)) makeBuiltIn(value, name, options);\n  if (options.global) {\n    if (simple) O[key] = value;\n    else defineGlobalProperty(key, value);\n  } else {\n    try {\n      if (!options.unsafe) delete O[key];\n      else if (O[key]) simple = true;\n    } catch (error) { /* empty */ }\n    if (simple) O[key] = value;\n    else definePropertyModule.f(O, key, {\n      value: value,\n      enumerable: false,\n      configurable: !options.nonConfigurable,\n      writable: !options.nonWritable\n    });\n  } return O;\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/define-built-in.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/define-built-ins.js"
/*!************************************************************!*\
  !*** ./node_modules/core-js/internals/define-built-ins.js ***!
  \************************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar defineBuiltIn = __webpack_require__(/*! ../internals/define-built-in */ \"./node_modules/core-js/internals/define-built-in.js\");\n\nmodule.exports = function (target, src, options) {\n  for (var key in src) defineBuiltIn(target, key, src[key], options);\n  return target;\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/define-built-ins.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/define-global-property.js"
/*!******************************************************************!*\
  !*** ./node_modules/core-js/internals/define-global-property.js ***!
  \******************************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar globalThis = __webpack_require__(/*! ../internals/global-this */ \"./node_modules/core-js/internals/global-this.js\");\n\n// eslint-disable-next-line es/no-object-defineproperty -- safe\nvar defineProperty = Object.defineProperty;\n\nmodule.exports = function (key, value) {\n  try {\n    defineProperty(globalThis, key, { value: value, configurable: true, writable: true });\n  } catch (error) {\n    globalThis[key] = value;\n  } return value;\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/define-global-property.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/descriptors.js"
/*!*******************************************************!*\
  !*** ./node_modules/core-js/internals/descriptors.js ***!
  \*******************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar fails = __webpack_require__(/*! ../internals/fails */ \"./node_modules/core-js/internals/fails.js\");\n\n// Detect IE8's incomplete defineProperty implementation\nmodule.exports = !fails(function () {\n  // eslint-disable-next-line es/no-object-defineproperty -- required for testing\n  return Object.defineProperty({}, 1, { get: function () { return 7; } })[1] !== 7;\n});\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/descriptors.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/detach-transferable.js"
/*!***************************************************************!*\
  !*** ./node_modules/core-js/internals/detach-transferable.js ***!
  \***************************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar globalThis = __webpack_require__(/*! ../internals/global-this */ \"./node_modules/core-js/internals/global-this.js\");\nvar getBuiltInNodeModule = __webpack_require__(/*! ../internals/get-built-in-node-module */ \"./node_modules/core-js/internals/get-built-in-node-module.js\");\nvar PROPER_STRUCTURED_CLONE_TRANSFER = __webpack_require__(/*! ../internals/structured-clone-proper-transfer */ \"./node_modules/core-js/internals/structured-clone-proper-transfer.js\");\n\nvar structuredClone = globalThis.structuredClone;\nvar $ArrayBuffer = globalThis.ArrayBuffer;\nvar $MessageChannel = globalThis.MessageChannel;\nvar detach = false;\nvar WorkerThreads, channel, buffer, $detach;\n\nif (PROPER_STRUCTURED_CLONE_TRANSFER) {\n  detach = function (transferable) {\n    structuredClone(transferable, { transfer: [transferable] });\n  };\n} else if ($ArrayBuffer) try {\n  if (!$MessageChannel) {\n    WorkerThreads = getBuiltInNodeModule('worker_threads');\n    if (WorkerThreads) $MessageChannel = WorkerThreads.MessageChannel;\n  }\n\n  if ($MessageChannel) {\n    channel = new $MessageChannel();\n    buffer = new $ArrayBuffer(2);\n\n    $detach = function (transferable) {\n      channel.port1.postMessage(null, [transferable]);\n    };\n\n    if (buffer.byteLength === 2) {\n      $detach(buffer);\n      if (buffer.byteLength === 0) detach = $detach;\n    }\n  }\n} catch (error) { /* empty */ }\n\nmodule.exports = detach;\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/detach-transferable.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/document-create-element.js"
/*!*******************************************************************!*\
  !*** ./node_modules/core-js/internals/document-create-element.js ***!
  \*******************************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar globalThis = __webpack_require__(/*! ../internals/global-this */ \"./node_modules/core-js/internals/global-this.js\");\nvar isObject = __webpack_require__(/*! ../internals/is-object */ \"./node_modules/core-js/internals/is-object.js\");\n\nvar document = globalThis.document;\n// typeof document.createElement is 'object' in old IE\nvar EXISTS = isObject(document) && isObject(document.createElement);\n\nmodule.exports = function (it) {\n  return EXISTS ? document.createElement(it) : {};\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/document-create-element.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/dom-exception-constants.js"
/*!*******************************************************************!*\
  !*** ./node_modules/core-js/internals/dom-exception-constants.js ***!
  \*******************************************************************/
(module) {

eval("{\nmodule.exports = {\n  IndexSizeError: { s: 'INDEX_SIZE_ERR', c: 1, m: 1 },\n  DOMStringSizeError: { s: 'DOMSTRING_SIZE_ERR', c: 2, m: 0 },\n  HierarchyRequestError: { s: 'HIERARCHY_REQUEST_ERR', c: 3, m: 1 },\n  WrongDocumentError: { s: 'WRONG_DOCUMENT_ERR', c: 4, m: 1 },\n  InvalidCharacterError: { s: 'INVALID_CHARACTER_ERR', c: 5, m: 1 },\n  NoDataAllowedError: { s: 'NO_DATA_ALLOWED_ERR', c: 6, m: 0 },\n  NoModificationAllowedError: { s: 'NO_MODIFICATION_ALLOWED_ERR', c: 7, m: 1 },\n  NotFoundError: { s: 'NOT_FOUND_ERR', c: 8, m: 1 },\n  NotSupportedError: { s: 'NOT_SUPPORTED_ERR', c: 9, m: 1 },\n  InUseAttributeError: { s: 'INUSE_ATTRIBUTE_ERR', c: 10, m: 1 },\n  InvalidStateError: { s: 'INVALID_STATE_ERR', c: 11, m: 1 },\n  SyntaxError: { s: 'SYNTAX_ERR', c: 12, m: 1 },\n  InvalidModificationError: { s: 'INVALID_MODIFICATION_ERR', c: 13, m: 1 },\n  NamespaceError: { s: 'NAMESPACE_ERR', c: 14, m: 1 },\n  InvalidAccessError: { s: 'INVALID_ACCESS_ERR', c: 15, m: 1 },\n  ValidationError: { s: 'VALIDATION_ERR', c: 16, m: 0 },\n  TypeMismatchError: { s: 'TYPE_MISMATCH_ERR', c: 17, m: 1 },\n  SecurityError: { s: 'SECURITY_ERR', c: 18, m: 1 },\n  NetworkError: { s: 'NETWORK_ERR', c: 19, m: 1 },\n  AbortError: { s: 'ABORT_ERR', c: 20, m: 1 },\n  URLMismatchError: { s: 'URL_MISMATCH_ERR', c: 21, m: 1 },\n  QuotaExceededError: { s: 'QUOTA_EXCEEDED_ERR', c: 22, m: 1 },\n  TimeoutError: { s: 'TIMEOUT_ERR', c: 23, m: 1 },\n  InvalidNodeTypeError: { s: 'INVALID_NODE_TYPE_ERR', c: 24, m: 1 },\n  DataCloneError: { s: 'DATA_CLONE_ERR', c: 25, m: 1 }\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/dom-exception-constants.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/entry-unbind.js"
/*!********************************************************!*\
  !*** ./node_modules/core-js/internals/entry-unbind.js ***!
  \********************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar globalThis = __webpack_require__(/*! ../internals/global-this */ \"./node_modules/core-js/internals/global-this.js\");\nvar uncurryThis = __webpack_require__(/*! ../internals/function-uncurry-this */ \"./node_modules/core-js/internals/function-uncurry-this.js\");\n\nmodule.exports = function (CONSTRUCTOR, METHOD) {\n  return uncurryThis(globalThis[CONSTRUCTOR].prototype[METHOD]);\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/entry-unbind.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/enum-bug-keys.js"
/*!*********************************************************!*\
  !*** ./node_modules/core-js/internals/enum-bug-keys.js ***!
  \*********************************************************/
(module) {

eval("{\n// IE8- don't enum bug keys\nmodule.exports = [\n  'constructor',\n  'hasOwnProperty',\n  'isPrototypeOf',\n  'propertyIsEnumerable',\n  'toLocaleString',\n  'toString',\n  'valueOf'\n];\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/enum-bug-keys.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/environment-is-node.js"
/*!***************************************************************!*\
  !*** ./node_modules/core-js/internals/environment-is-node.js ***!
  \***************************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar ENVIRONMENT = __webpack_require__(/*! ../internals/environment */ \"./node_modules/core-js/internals/environment.js\");\n\nmodule.exports = ENVIRONMENT === 'NODE';\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/environment-is-node.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/environment-user-agent.js"
/*!******************************************************************!*\
  !*** ./node_modules/core-js/internals/environment-user-agent.js ***!
  \******************************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar globalThis = __webpack_require__(/*! ../internals/global-this */ \"./node_modules/core-js/internals/global-this.js\");\n\nvar navigator = globalThis.navigator;\nvar userAgent = navigator && navigator.userAgent;\n\nmodule.exports = userAgent ? String(userAgent) : '';\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/environment-user-agent.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/environment-v8-version.js"
/*!******************************************************************!*\
  !*** ./node_modules/core-js/internals/environment-v8-version.js ***!
  \******************************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar globalThis = __webpack_require__(/*! ../internals/global-this */ \"./node_modules/core-js/internals/global-this.js\");\nvar userAgent = __webpack_require__(/*! ../internals/environment-user-agent */ \"./node_modules/core-js/internals/environment-user-agent.js\");\n\nvar process = globalThis.process;\nvar Deno = globalThis.Deno;\nvar versions = process && process.versions || Deno && Deno.version;\nvar v8 = versions && versions.v8;\nvar match, version;\n\nif (v8) {\n  match = v8.split('.');\n  // in old Chrome, versions of V8 isn't V8 = Chrome / 10\n  // but their correct versions are not interesting for us\n  version = match[0] > 0 && match[0] < 4 ? 1 : +(match[0] + match[1]);\n}\n\n// BrowserFS NodeJS `process` polyfill incorrectly set `.v8` to `0.0`\n// so check `userAgent` even if `.v8` exists, but 0\nif (!version && userAgent) {\n  match = userAgent.match(/Edge\\/(\\d+)/);\n  if (!match || match[1] >= 74) {\n    match = userAgent.match(/Chrome\\/(\\d+)/);\n    if (match) version = +match[1];\n  }\n}\n\nmodule.exports = version;\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/environment-v8-version.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/environment.js"
/*!*******************************************************!*\
  !*** ./node_modules/core-js/internals/environment.js ***!
  \*******************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\n/* global Bun, Deno -- detection */\nvar globalThis = __webpack_require__(/*! ../internals/global-this */ \"./node_modules/core-js/internals/global-this.js\");\nvar userAgent = __webpack_require__(/*! ../internals/environment-user-agent */ \"./node_modules/core-js/internals/environment-user-agent.js\");\nvar classof = __webpack_require__(/*! ../internals/classof-raw */ \"./node_modules/core-js/internals/classof-raw.js\");\n\nvar userAgentStartsWith = function (string) {\n  return userAgent.slice(0, string.length) === string;\n};\n\nmodule.exports = (function () {\n  if (userAgentStartsWith('Bun/')) return 'BUN';\n  if (userAgentStartsWith('Cloudflare-Workers')) return 'CLOUDFLARE';\n  if (userAgentStartsWith('Deno/')) return 'DENO';\n  if (userAgentStartsWith('Node.js/')) return 'NODE';\n  if (globalThis.Bun && typeof Bun.version == 'string') return 'BUN';\n  if (globalThis.Deno && typeof Deno.version == 'object') return 'DENO';\n  if (classof(globalThis.process) === 'process') return 'NODE';\n  if (globalThis.window && globalThis.document) return 'BROWSER';\n  return 'REST';\n})();\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/environment.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/error-stack-clear.js"
/*!*************************************************************!*\
  !*** ./node_modules/core-js/internals/error-stack-clear.js ***!
  \*************************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar uncurryThis = __webpack_require__(/*! ../internals/function-uncurry-this */ \"./node_modules/core-js/internals/function-uncurry-this.js\");\n\nvar $Error = Error;\nvar replace = uncurryThis(''.replace);\n\nvar TEST = (function (arg) { return String(new $Error(arg).stack); })('zxcasd');\n// eslint-disable-next-line redos/no-vulnerable, sonarjs/slow-regex -- safe\nvar V8_OR_CHAKRA_STACK_ENTRY = /\\n\\s*at [^:]*:[^\\n]*/;\nvar IS_V8_OR_CHAKRA_STACK = V8_OR_CHAKRA_STACK_ENTRY.test(TEST);\n\nmodule.exports = function (stack, dropEntries) {\n  if (IS_V8_OR_CHAKRA_STACK && typeof stack == 'string' && !$Error.prepareStackTrace) {\n    while (dropEntries--) stack = replace(stack, V8_OR_CHAKRA_STACK_ENTRY, '');\n  } return stack;\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/error-stack-clear.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/error-stack-installable.js"
/*!*******************************************************************!*\
  !*** ./node_modules/core-js/internals/error-stack-installable.js ***!
  \*******************************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar fails = __webpack_require__(/*! ../internals/fails */ \"./node_modules/core-js/internals/fails.js\");\nvar createPropertyDescriptor = __webpack_require__(/*! ../internals/create-property-descriptor */ \"./node_modules/core-js/internals/create-property-descriptor.js\");\n\nmodule.exports = !fails(function () {\n  var error = new Error('a');\n  if (!('stack' in error)) return true;\n  // eslint-disable-next-line es/no-object-defineproperty -- safe\n  Object.defineProperty(error, 'stack', createPropertyDescriptor(1, 7));\n  return error.stack !== 7;\n});\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/error-stack-installable.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/error-to-string.js"
/*!***********************************************************!*\
  !*** ./node_modules/core-js/internals/error-to-string.js ***!
  \***********************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar DESCRipTORS = __webpack_require__(/*! ../internals/descriptors */ \"./node_modules/core-js/internals/descriptors.js\");\nvar fails = __webpack_require__(/*! ../internals/fails */ \"./node_modules/core-js/internals/fails.js\");\nvar anObject = __webpack_require__(/*! ../internals/an-object */ \"./node_modules/core-js/internals/an-object.js\");\nvar normalizeStringArgument = __webpack_require__(/*! ../internals/normalize-string-argument */ \"./node_modules/core-js/internals/normalize-string-argument.js\");\n\nvar nativeErrorToString = Error.prototype.toString;\n\nvar INCORRECT_TO_STRING = fails(function () {\n  if (DESCRipTORS) {\n    // Chrome 32- incorrectly call accessor\n    // eslint-disable-next-line es/no-object-create, es/no-object-defineproperty -- safe\n    var object = Object.create(Object.defineProperty({}, 'name', { get: function () {\n      return this === object;\n    } }));\n    if (nativeErrorToString.call(object) !== 'true') return true;\n  }\n  // FF10- does not properly handle non-strings\n  return nativeErrorToString.call({ message: 1, name: 2 }) !== '2: 1'\n    // IE8 does not properly handle defaults\n    || nativeErrorToString.call({}) !== 'Error';\n});\n\nmodule.exports = INCORRECT_TO_STRING ? function toString() {\n  var O = anObject(this);\n  var name = normalizeStringArgument(O.name, 'Error');\n  var message = normalizeStringArgument(O.message);\n  return !name ? message : !message ? name : name + ': ' + message;\n} : nativeErrorToString;\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/error-to-string.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/export.js"
/*!**************************************************!*\
  !*** ./node_modules/core-js/internals/export.js ***!
  \**************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar globalThis = __webpack_require__(/*! ../internals/global-this */ \"./node_modules/core-js/internals/global-this.js\");\nvar getOwnPropertyDescriptor = (__webpack_require__(/*! ../internals/object-get-own-property-descriptor */ \"./node_modules/core-js/internals/object-get-own-property-descriptor.js\").f);\nvar createNonEnumerableProperty = __webpack_require__(/*! ../internals/create-non-enumerable-property */ \"./node_modules/core-js/internals/create-non-enumerable-property.js\");\nvar defineBuiltIn = __webpack_require__(/*! ../internals/define-built-in */ \"./node_modules/core-js/internals/define-built-in.js\");\nvar defineGlobalProperty = __webpack_require__(/*! ../internals/define-global-property */ \"./node_modules/core-js/internals/define-global-property.js\");\nvar copyConstructorProperties = __webpack_require__(/*! ../internals/copy-constructor-properties */ \"./node_modules/core-js/internals/copy-constructor-properties.js\");\nvar isForced = __webpack_require__(/*! ../internals/is-forced */ \"./node_modules/core-js/internals/is-forced.js\");\n\n/*\n  options.target         - name of the target object\n  options.global         - target is the global object\n  options.stat           - export as static methods of target\n  options.proto          - export as prototype methods of target\n  options.real           - real prototype method for the `pure` version\n  options.forced         - export even if the native feature is available\n  options.bind           - bind methods to the target, required for the `pure` version\n  options.wrap           - wrap constructors to preventing global pollution, required for the `pure` version\n  options.unsafe         - use the simple assignment of property instead of delete + defineProperty\n  options.sham           - add a flag to not completely full polyfills\n  options.enumerable     - export as enumerable property\n  options.dontCallGetSet - prevent calling a getter on target\n  options.name           - the .name of the function if it does not match the key\n*/\nmodule.exports = function (options, source) {\n  var TARGET = options.target;\n  var GLOBAL = options.global;\n  var STATIC = options.stat;\n  var FORCED, target, key, targetProperty, sourceProperty, descriptor;\n  if (GLOBAL) {\n    target = globalThis;\n  } else if (STATIC) {\n    target = globalThis[TARGET] || defineGlobalProperty(TARGET, {});\n  } else {\n    target = globalThis[TARGET] && globalThis[TARGET].prototype;\n  }\n  if (target) for (key in source) {\n    sourceProperty = source[key];\n    if (options.dontCallGetSet) {\n      descriptor = getOwnPropertyDescriptor(target, key);\n      targetProperty = descriptor && descriptor.value;\n    } else targetProperty = target[key];\n    FORCED = isForced(GLOBAL ? key : TARGET + (STATIC ? '.' : '#') + key, options.forced);\n    // contained in target\n    if (!FORCED && targetProperty !== undefined) {\n      if (typeof sourceProperty == typeof targetProperty) continue;\n      copyConstructorProperties(sourceProperty, targetProperty);\n    }\n    // add a flag to not completely full polyfills\n    if (options.sham || (targetProperty && targetProperty.sham)) {\n      createNonEnumerableProperty(sourceProperty, 'sham', true);\n    }\n    defineBuiltIn(target, key, sourceProperty, options);\n  }\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/export.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/fails.js"
/*!*************************************************!*\
  !*** ./node_modules/core-js/internals/fails.js ***!
  \*************************************************/
(module) {

eval("{\nmodule.exports = function (exec) {\n  try {\n    return !!exec();\n  } catch (error) {\n    return true;\n  }\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/fails.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/freezing.js"
/*!****************************************************!*\
  !*** ./node_modules/core-js/internals/freezing.js ***!
  \****************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar fails = __webpack_require__(/*! ../internals/fails */ \"./node_modules/core-js/internals/fails.js\");\n\nmodule.exports = !fails(function () {\n  // eslint-disable-next-line es/no-object-isextensible, es/no-object-preventextensions -- required for testing\n  return Object.isExtensible(Object.preventExtensions({}));\n});\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/freezing.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/function-bind-context.js"
/*!*****************************************************************!*\
  !*** ./node_modules/core-js/internals/function-bind-context.js ***!
  \*****************************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar uncurryThis = __webpack_require__(/*! ../internals/function-uncurry-this-clause */ \"./node_modules/core-js/internals/function-uncurry-this-clause.js\");\nvar aCallable = __webpack_require__(/*! ../internals/a-callable */ \"./node_modules/core-js/internals/a-callable.js\");\nvar NATIVE_BIND = __webpack_require__(/*! ../internals/function-bind-native */ \"./node_modules/core-js/internals/function-bind-native.js\");\n\nvar bind = uncurryThis(uncurryThis.bind);\n\n// optional / simple context binding\nmodule.exports = function (fn, that) {\n  aCallable(fn);\n  return that === undefined ? fn : NATIVE_BIND ? bind(fn, that) : function (/* ...args */) {\n    return fn.apply(that, arguments);\n  };\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/function-bind-context.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/function-bind-native.js"
/*!****************************************************************!*\
  !*** ./node_modules/core-js/internals/function-bind-native.js ***!
  \****************************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar fails = __webpack_require__(/*! ../internals/fails */ \"./node_modules/core-js/internals/fails.js\");\n\nmodule.exports = !fails(function () {\n  // eslint-disable-next-line es/no-function-prototype-bind -- safe\n  var test = function () { /* empty */ }.bind();\n  // eslint-disable-next-line no-prototype-builtins -- safe\n  return typeof test != 'function' || test.hasOwnProperty('prototype');\n});\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/function-bind-native.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/function-call.js"
/*!*********************************************************!*\
  !*** ./node_modules/core-js/internals/function-call.js ***!
  \*********************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar NATIVE_BIND = __webpack_require__(/*! ../internals/function-bind-native */ \"./node_modules/core-js/internals/function-bind-native.js\");\n\nvar call = Function.prototype.call;\n// eslint-disable-next-line es/no-function-prototype-bind -- safe\nmodule.exports = NATIVE_BIND ? call.bind(call) : function () {\n  return call.apply(call, arguments);\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/function-call.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/function-name.js"
/*!*********************************************************!*\
  !*** ./node_modules/core-js/internals/function-name.js ***!
  \*********************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar DESCRipTORS = __webpack_require__(/*! ../internals/descriptors */ \"./node_modules/core-js/internals/descriptors.js\");\nvar hasOwn = __webpack_require__(/*! ../internals/has-own-property */ \"./node_modules/core-js/internals/has-own-property.js\");\n\nvar FunctionPrototype = Function.prototype;\n// eslint-disable-next-line es/no-object-getownpropertydescriptor -- safe\nvar getDescriptor = DESCRipTORS && Object.getOwnPropertyDescriptor;\n\nvar EXISTS = hasOwn(FunctionPrototype, 'name');\n// additional protection from minified / mangled / dropped function names\nvar PROPER = EXISTS && function something() { /* empty */ }.name === 'something';\nvar CONFIGURABLE = EXISTS && (!DESCRipTORS || (DESCRipTORS && getDescriptor(FunctionPrototype, 'name').configurable));\n\nmodule.exports = {\n  EXISTS: EXISTS,\n  PROPER: PROPER,\n  CONFIGURABLE: CONFIGURABLE\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/function-name.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/function-uncurry-this-accessor.js"
/*!**************************************************************************!*\
  !*** ./node_modules/core-js/internals/function-uncurry-this-accessor.js ***!
  \**************************************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar uncurryThis = __webpack_require__(/*! ../internals/function-uncurry-this */ \"./node_modules/core-js/internals/function-uncurry-this.js\");\nvar aCallable = __webpack_require__(/*! ../internals/a-callable */ \"./node_modules/core-js/internals/a-callable.js\");\n\nmodule.exports = function (object, key, method) {\n  try {\n    // eslint-disable-next-line es/no-object-getownpropertydescriptor -- safe\n    return uncurryThis(aCallable(Object.getOwnPropertyDescriptor(object, key)[method]));\n  } catch (error) { /* empty */ }\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/function-uncurry-this-accessor.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/function-uncurry-this-clause.js"
/*!************************************************************************!*\
  !*** ./node_modules/core-js/internals/function-uncurry-this-clause.js ***!
  \************************************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar classofRaw = __webpack_require__(/*! ../internals/classof-raw */ \"./node_modules/core-js/internals/classof-raw.js\");\nvar uncurryThis = __webpack_require__(/*! ../internals/function-uncurry-this */ \"./node_modules/core-js/internals/function-uncurry-this.js\");\n\nmodule.exports = function (fn) {\n  // Nashorn bug:\n  //   https://github.com/zloirock/core-js/issues/1128\n  //   https://github.com/zloirock/core-js/issues/1130\n  if (classofRaw(fn) === 'Function') return uncurryThis(fn);\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/function-uncurry-this-clause.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/function-uncurry-this.js"
/*!*****************************************************************!*\
  !*** ./node_modules/core-js/internals/function-uncurry-this.js ***!
  \*****************************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar NATIVE_BIND = __webpack_require__(/*! ../internals/function-bind-native */ \"./node_modules/core-js/internals/function-bind-native.js\");\n\nvar FunctionPrototype = Function.prototype;\nvar call = FunctionPrototype.call;\n// eslint-disable-next-line es/no-function-prototype-bind -- safe\nvar uncurryThisWithBind = NATIVE_BIND && FunctionPrototype.bind.bind(call, call);\n\nmodule.exports = NATIVE_BIND ? uncurryThisWithBind : function (fn) {\n  return function () {\n    return call.apply(fn, arguments);\n  };\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/function-uncurry-this.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/get-built-in-node-module.js"
/*!********************************************************************!*\
  !*** ./node_modules/core-js/internals/get-built-in-node-module.js ***!
  \********************************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar globalThis = __webpack_require__(/*! ../internals/global-this */ \"./node_modules/core-js/internals/global-this.js\");\nvar IS_NODE = __webpack_require__(/*! ../internals/environment-is-node */ \"./node_modules/core-js/internals/environment-is-node.js\");\n\nmodule.exports = function (name) {\n  if (IS_NODE) {\n    try {\n      return globalThis.process.getBuiltinModule(name);\n    } catch (error) { /* empty */ }\n    try {\n      // eslint-disable-next-line no-new-func -- safe\n      return Function('return require(\"' + name + '\")')();\n    } catch (error) { /* empty */ }\n  }\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/get-built-in-node-module.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/get-built-in.js"
/*!********************************************************!*\
  !*** ./node_modules/core-js/internals/get-built-in.js ***!
  \********************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar globalThis = __webpack_require__(/*! ../internals/global-this */ \"./node_modules/core-js/internals/global-this.js\");\nvar isCallable = __webpack_require__(/*! ../internals/is-callable */ \"./node_modules/core-js/internals/is-callable.js\");\n\nvar aFunction = function (argument) {\n  return isCallable(argument) ? argument : undefined;\n};\n\nmodule.exports = function (namespace, method) {\n  return arguments.length < 2 ? aFunction(globalThis[namespace]) : globalThis[namespace] && globalThis[namespace][method];\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/get-built-in.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/get-iterator-method.js"
/*!***************************************************************!*\
  !*** ./node_modules/core-js/internals/get-iterator-method.js ***!
  \***************************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar classof = __webpack_require__(/*! ../internals/classof */ \"./node_modules/core-js/internals/classof.js\");\nvar getMethod = __webpack_require__(/*! ../internals/get-method */ \"./node_modules/core-js/internals/get-method.js\");\nvar isNullOrUndefined = __webpack_require__(/*! ../internals/is-null-or-undefined */ \"./node_modules/core-js/internals/is-null-or-undefined.js\");\nvar Iterators = __webpack_require__(/*! ../internals/iterators */ \"./node_modules/core-js/internals/iterators.js\");\nvar wellKnownSymbol = __webpack_require__(/*! ../internals/well-known-symbol */ \"./node_modules/core-js/internals/well-known-symbol.js\");\n\nvar ITERATOR = wellKnownSymbol('iterator');\n\nmodule.exports = function (it) {\n  if (!isNullOrUndefined(it)) return getMethod(it, ITERATOR)\n    || getMethod(it, '@@iterator')\n    || Iterators[classof(it)];\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/get-iterator-method.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/get-iterator.js"
/*!********************************************************!*\
  !*** ./node_modules/core-js/internals/get-iterator.js ***!
  \********************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar call = __webpack_require__(/*! ../internals/function-call */ \"./node_modules/core-js/internals/function-call.js\");\nvar aCallable = __webpack_require__(/*! ../internals/a-callable */ \"./node_modules/core-js/internals/a-callable.js\");\nvar anObject = __webpack_require__(/*! ../internals/an-object */ \"./node_modules/core-js/internals/an-object.js\");\nvar tryToString = __webpack_require__(/*! ../internals/try-to-string */ \"./node_modules/core-js/internals/try-to-string.js\");\nvar getIteratorMethod = __webpack_require__(/*! ../internals/get-iterator-method */ \"./node_modules/core-js/internals/get-iterator-method.js\");\n\nvar $TypeError = TypeError;\n\nmodule.exports = function (argument, usingIterator) {\n  var iteratorMethod = arguments.length < 2 ? getIteratorMethod(argument) : usingIterator;\n  if (aCallable(iteratorMethod)) return anObject(call(iteratorMethod, argument));\n  throw new $TypeError(tryToString(argument) + ' is not iterable');\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/get-iterator.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/get-method.js"
/*!******************************************************!*\
  !*** ./node_modules/core-js/internals/get-method.js ***!
  \******************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar aCallable = __webpack_require__(/*! ../internals/a-callable */ \"./node_modules/core-js/internals/a-callable.js\");\nvar isNullOrUndefined = __webpack_require__(/*! ../internals/is-null-or-undefined */ \"./node_modules/core-js/internals/is-null-or-undefined.js\");\n\n// `GetMethod` abstract operation\n// https://tc39.es/ecma262/#sec-getmethod\nmodule.exports = function (V, P) {\n  var func = V[P];\n  return isNullOrUndefined(func) ? undefined : aCallable(func);\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/get-method.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/global-this.js"
/*!*******************************************************!*\
  !*** ./node_modules/core-js/internals/global-this.js ***!
  \*******************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar check = function (it) {\n  return it && it.Math === Math && it;\n};\n\n// https://github.com/zloirock/core-js/issues/86#issuecomment-115759028\nmodule.exports =\n  // eslint-disable-next-line es/no-global-this -- safe\n  check(typeof globalThis == 'object' && globalThis) ||\n  check(typeof window == 'object' && window) ||\n  // eslint-disable-next-line no-restricted-globals -- safe\n  check(typeof self == 'object' && self) ||\n  check(typeof __webpack_require__.g == 'object' && __webpack_require__.g) ||\n  check(typeof this == 'object' && this) ||\n  // eslint-disable-next-line no-new-func -- fallback\n  (function () { return this; })() || Function('return this')();\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/global-this.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/has-own-property.js"
/*!************************************************************!*\
  !*** ./node_modules/core-js/internals/has-own-property.js ***!
  \************************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar uncurryThis = __webpack_require__(/*! ../internals/function-uncurry-this */ \"./node_modules/core-js/internals/function-uncurry-this.js\");\nvar toObject = __webpack_require__(/*! ../internals/to-object */ \"./node_modules/core-js/internals/to-object.js\");\n\nvar hasOwnProperty = uncurryThis({}.hasOwnProperty);\n\n// `HasOwnProperty` abstract operation\n// https://tc39.es/ecma262/#sec-hasownproperty\n// eslint-disable-next-line es/no-object-hasown -- safe\nmodule.exports = Object.hasOwn || function hasOwn(it, key) {\n  return hasOwnProperty(toObject(it), key);\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/has-own-property.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/hidden-keys.js"
/*!*******************************************************!*\
  !*** ./node_modules/core-js/internals/hidden-keys.js ***!
  \*******************************************************/
(module) {

eval("{\nmodule.exports = {};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/hidden-keys.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/html.js"
/*!************************************************!*\
  !*** ./node_modules/core-js/internals/html.js ***!
  \************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar getBuiltIn = __webpack_require__(/*! ../internals/get-built-in */ \"./node_modules/core-js/internals/get-built-in.js\");\n\nmodule.exports = getBuiltIn('document', 'documentElement');\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/html.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/ie8-dom-define.js"
/*!**********************************************************!*\
  !*** ./node_modules/core-js/internals/ie8-dom-define.js ***!
  \**********************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar DESCRipTORS = __webpack_require__(/*! ../internals/descriptors */ \"./node_modules/core-js/internals/descriptors.js\");\nvar fails = __webpack_require__(/*! ../internals/fails */ \"./node_modules/core-js/internals/fails.js\");\nvar createElement = __webpack_require__(/*! ../internals/document-create-element */ \"./node_modules/core-js/internals/document-create-element.js\");\n\n// Thanks to IE8 for its funny defineProperty\nmodule.exports = !DESCRipTORS && !fails(function () {\n  // eslint-disable-next-line es/no-object-defineproperty -- required for testing\n  return Object.defineProperty(createElement('div'), 'a', {\n    get: function () { return 7; }\n  }).a !== 7;\n});\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/ie8-dom-define.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/indexed-object.js"
/*!**********************************************************!*\
  !*** ./node_modules/core-js/internals/indexed-object.js ***!
  \**********************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar uncurryThis = __webpack_require__(/*! ../internals/function-uncurry-this */ \"./node_modules/core-js/internals/function-uncurry-this.js\");\nvar fails = __webpack_require__(/*! ../internals/fails */ \"./node_modules/core-js/internals/fails.js\");\nvar classof = __webpack_require__(/*! ../internals/classof-raw */ \"./node_modules/core-js/internals/classof-raw.js\");\n\nvar $Object = Object;\nvar split = uncurryThis(''.split);\n\n// fallback for non-array-like ES3 and non-enumerable old V8 strings\nmodule.exports = fails(function () {\n  // throws an error in rhino, see https://github.com/mozilla/rhino/issues/346\n  // eslint-disable-next-line no-prototype-builtins -- safe\n  return !$Object('z').propertyIsEnumerable(0);\n}) ? function (it) {\n  return classof(it) === 'String' ? split(it, '') : $Object(it);\n} : $Object;\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/indexed-object.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/inherit-if-required.js"
/*!***************************************************************!*\
  !*** ./node_modules/core-js/internals/inherit-if-required.js ***!
  \***************************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar isCallable = __webpack_require__(/*! ../internals/is-callable */ \"./node_modules/core-js/internals/is-callable.js\");\nvar isObject = __webpack_require__(/*! ../internals/is-object */ \"./node_modules/core-js/internals/is-object.js\");\nvar setPrototypeOf = __webpack_require__(/*! ../internals/object-set-prototype-of */ \"./node_modules/core-js/internals/object-set-prototype-of.js\");\n\n// makes subclassing work correct for wrapped built-ins\nmodule.exports = function ($this, dummy, Wrapper) {\n  var NewTarget, NewTargetPrototype;\n  if (\n    // it can work only with native `setPrototypeOf`\n    setPrototypeOf &&\n    // we haven't completely correct pre-ES6 way for getting `new.target`, so use this\n    isCallable(NewTarget = dummy.constructor) &&\n    NewTarget !== Wrapper &&\n    isObject(NewTargetPrototype = NewTarget.prototype) &&\n    NewTargetPrototype !== Wrapper.prototype\n  ) setPrototypeOf($this, NewTargetPrototype);\n  return $this;\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/inherit-if-required.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/inspect-source.js"
/*!**********************************************************!*\
  !*** ./node_modules/core-js/internals/inspect-source.js ***!
  \**********************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar uncurryThis = __webpack_require__(/*! ../internals/function-uncurry-this */ \"./node_modules/core-js/internals/function-uncurry-this.js\");\nvar isCallable = __webpack_require__(/*! ../internals/is-callable */ \"./node_modules/core-js/internals/is-callable.js\");\nvar store = __webpack_require__(/*! ../internals/shared-store */ \"./node_modules/core-js/internals/shared-store.js\");\n\nvar functionToString = uncurryThis(Function.toString);\n\n// this helper broken in `core-js@3.4.1-3.4.4`, so we can't use `shared` helper\nif (!isCallable(store.inspectSource)) {\n  store.inspectSource = function (it) {\n    return functionToString(it);\n  };\n}\n\nmodule.exports = store.inspectSource;\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/inspect-source.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/internal-metadata.js"
/*!*************************************************************!*\
  !*** ./node_modules/core-js/internals/internal-metadata.js ***!
  \*************************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar $ = __webpack_require__(/*! ../internals/export */ \"./node_modules/core-js/internals/export.js\");\nvar uncurryThis = __webpack_require__(/*! ../internals/function-uncurry-this */ \"./node_modules/core-js/internals/function-uncurry-this.js\");\nvar hiddenKeys = __webpack_require__(/*! ../internals/hidden-keys */ \"./node_modules/core-js/internals/hidden-keys.js\");\nvar isObject = __webpack_require__(/*! ../internals/is-object */ \"./node_modules/core-js/internals/is-object.js\");\nvar hasOwn = __webpack_require__(/*! ../internals/has-own-property */ \"./node_modules/core-js/internals/has-own-property.js\");\nvar defineProperty = (__webpack_require__(/*! ../internals/object-define-property */ \"./node_modules/core-js/internals/object-define-property.js\").f);\nvar getOwnPropertyNamesModule = __webpack_require__(/*! ../internals/object-get-own-property-names */ \"./node_modules/core-js/internals/object-get-own-property-names.js\");\nvar getOwnPropertyNamesExternalModule = __webpack_require__(/*! ../internals/object-get-own-property-names-external */ \"./node_modules/core-js/internals/object-get-own-property-names-external.js\");\nvar isExtensible = __webpack_require__(/*! ../internals/object-is-extensible */ \"./node_modules/core-js/internals/object-is-extensible.js\");\nvar uid = __webpack_require__(/*! ../internals/uid */ \"./node_modules/core-js/internals/uid.js\");\nvar FREEZING = __webpack_require__(/*! ../internals/freezing */ \"./node_modules/core-js/internals/freezing.js\");\n\nvar REQUIRED = false;\nvar METADATA = uid('meta');\nvar id = 0;\n\nvar setMetadata = function (it) {\n  defineProperty(it, METADATA, { value: {\n    objectID: 'O' + id++, // object ID\n    weakData: {}          // weak collections IDs\n  } });\n};\n\nvar fastKey = function (it, create) {\n  // return a primitive with prefix\n  if (!isObject(it)) return typeof it == 'symbol' ? it : (typeof it == 'string' ? 'S' : 'P') + it;\n  if (!hasOwn(it, METADATA)) {\n    // can't set metadata to uncaught frozen object\n    if (!isExtensible(it)) return 'F';\n    // not necessary to add metadata\n    if (!create) return 'E';\n    // add missing metadata\n    setMetadata(it);\n  // return object ID\n  } return it[METADATA].objectID;\n};\n\nvar getWeakData = function (it, create) {\n  if (!hasOwn(it, METADATA)) {\n    // can't set metadata to uncaught frozen object\n    if (!isExtensible(it)) return true;\n    // not necessary to add metadata\n    if (!create) return false;\n    // add missing metadata\n    setMetadata(it);\n  // return the store of weak collections IDs\n  } return it[METADATA].weakData;\n};\n\n// add metadata on freeze-family methods calling\nvar onFreeze = function (it) {\n  if (FREEZING && REQUIRED && isExtensible(it) && !hasOwn(it, METADATA)) setMetadata(it);\n  return it;\n};\n\nvar enable = function () {\n  meta.enable = function () { /* empty */ };\n  REQUIRED = true;\n  var getOwnPropertyNames = getOwnPropertyNamesModule.f;\n  var splice = uncurryThis([].splice);\n  var test = {};\n  // eslint-disable-next-line unicorn/no-immediate-mutation -- ES3 syntax limitation\n  test[METADATA] = 1;\n\n  // prevent exposing of metadata key\n  if (getOwnPropertyNames(test).length) {\n    getOwnPropertyNamesModule.f = function (it) {\n      var result = getOwnPropertyNames(it);\n      for (var i = 0, length = result.length; i < length; i++) {\n        if (result[i] === METADATA) {\n          splice(result, i, 1);\n          break;\n        }\n      } return result;\n    };\n\n    $({ target: 'Object', stat: true, forced: true }, {\n      getOwnPropertyNames: getOwnPropertyNamesExternalModule.f\n    });\n  }\n};\n\nvar meta = module.exports = {\n  enable: enable,\n  fastKey: fastKey,\n  getWeakData: getWeakData,\n  onFreeze: onFreeze\n};\n\nhiddenKeys[METADATA] = true;\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/internal-metadata.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/internal-state.js"
/*!**********************************************************!*\
  !*** ./node_modules/core-js/internals/internal-state.js ***!
  \**********************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar NATIVE_WEAK_MAP = __webpack_require__(/*! ../internals/weak-map-basic-detection */ \"./node_modules/core-js/internals/weak-map-basic-detection.js\");\nvar globalThis = __webpack_require__(/*! ../internals/global-this */ \"./node_modules/core-js/internals/global-this.js\");\nvar isObject = __webpack_require__(/*! ../internals/is-object */ \"./node_modules/core-js/internals/is-object.js\");\nvar createNonEnumerableProperty = __webpack_require__(/*! ../internals/create-non-enumerable-property */ \"./node_modules/core-js/internals/create-non-enumerable-property.js\");\nvar hasOwn = __webpack_require__(/*! ../internals/has-own-property */ \"./node_modules/core-js/internals/has-own-property.js\");\nvar shared = __webpack_require__(/*! ../internals/shared-store */ \"./node_modules/core-js/internals/shared-store.js\");\nvar sharedKey = __webpack_require__(/*! ../internals/shared-key */ \"./node_modules/core-js/internals/shared-key.js\");\nvar hiddenKeys = __webpack_require__(/*! ../internals/hidden-keys */ \"./node_modules/core-js/internals/hidden-keys.js\");\n\nvar OBJECT_ALREADY_INITIALIZED = 'Object already initialized';\nvar TypeError = globalThis.TypeError;\nvar WeakMap = globalThis.WeakMap;\nvar set, get, has;\n\nvar enforce = function (it) {\n  return has(it) ? get(it) : set(it, {});\n};\n\nvar getterFor = function (TYPE) {\n  return function (it) {\n    var state;\n    if (!isObject(it) || (state = get(it)).type !== TYPE) {\n      throw new TypeError('Incompatible receiver, ' + TYPE + ' required');\n    } return state;\n  };\n};\n\nif (NATIVE_WEAK_MAP || shared.state) {\n  var store = shared.state || (shared.state = new WeakMap());\n  /* eslint-disable no-self-assign -- prototype methods protection */\n  store.get = store.get;\n  store.has = store.has;\n  store.set = store.set;\n  /* eslint-enable no-self-assign -- prototype methods protection */\n  set = function (it, metadata) {\n    if (store.has(it)) throw new TypeError(OBJECT_ALREADY_INITIALIZED);\n    metadata.facade = it;\n    store.set(it, metadata);\n    return metadata;\n  };\n  get = function (it) {\n    return store.get(it) || {};\n  };\n  has = function (it) {\n    return store.has(it);\n  };\n} else {\n  var STATE = sharedKey('state');\n  hiddenKeys[STATE] = true;\n  set = function (it, metadata) {\n    if (hasOwn(it, STATE)) throw new TypeError(OBJECT_ALREADY_INITIALIZED);\n    metadata.facade = it;\n    createNonEnumerableProperty(it, STATE, metadata);\n    return metadata;\n  };\n  get = function (it) {\n    return hasOwn(it, STATE) ? it[STATE] : {};\n  };\n  has = function (it) {\n    return hasOwn(it, STATE);\n  };\n}\n\nmodule.exports = {\n  set: set,\n  get: get,\n  has: has,\n  enforce: enforce,\n  getterFor: getterFor\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/internal-state.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/is-array-iterator-method.js"
/*!********************************************************************!*\
  !*** ./node_modules/core-js/internals/is-array-iterator-method.js ***!
  \********************************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar wellKnownSymbol = __webpack_require__(/*! ../internals/well-known-symbol */ \"./node_modules/core-js/internals/well-known-symbol.js\");\nvar Iterators = __webpack_require__(/*! ../internals/iterators */ \"./node_modules/core-js/internals/iterators.js\");\n\nvar ITERATOR = wellKnownSymbol('iterator');\nvar ArrayPrototype = Array.prototype;\n\n// check on default Array iterator\nmodule.exports = function (it) {\n  return it !== undefined && (Iterators.Array === it || ArrayPrototype[ITERATOR] === it);\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/is-array-iterator-method.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/is-callable.js"
/*!*******************************************************!*\
  !*** ./node_modules/core-js/internals/is-callable.js ***!
  \*******************************************************/
(module) {

eval("{\n// https://tc39.es/ecma262/#sec-IsHTMLDDA-internal-slot\nvar documentAll = typeof document == 'object' && document.all;\n\n// `IsCallable` abstract operation\n// https://tc39.es/ecma262/#sec-iscallable\n// eslint-disable-next-line unicorn/no-typeof-undefined -- required for testing\nmodule.exports = typeof documentAll == 'undefined' && documentAll !== undefined ? function (argument) {\n  return typeof argument == 'function' || argument === documentAll;\n} : function (argument) {\n  return typeof argument == 'function';\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/is-callable.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/is-constructor.js"
/*!**********************************************************!*\
  !*** ./node_modules/core-js/internals/is-constructor.js ***!
  \**********************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar uncurryThis = __webpack_require__(/*! ../internals/function-uncurry-this */ \"./node_modules/core-js/internals/function-uncurry-this.js\");\nvar fails = __webpack_require__(/*! ../internals/fails */ \"./node_modules/core-js/internals/fails.js\");\nvar isCallable = __webpack_require__(/*! ../internals/is-callable */ \"./node_modules/core-js/internals/is-callable.js\");\nvar classof = __webpack_require__(/*! ../internals/classof */ \"./node_modules/core-js/internals/classof.js\");\nvar getBuiltIn = __webpack_require__(/*! ../internals/get-built-in */ \"./node_modules/core-js/internals/get-built-in.js\");\nvar inspectSource = __webpack_require__(/*! ../internals/inspect-source */ \"./node_modules/core-js/internals/inspect-source.js\");\n\nvar noop = function () { /* empty */ };\nvar construct = getBuiltIn('Reflect', 'construct');\nvar constructorRegExp = /^\\s*(?:class|function)\\b/;\nvar exec = uncurryThis(constructorRegExp.exec);\nvar INCORRECT_TO_STRING = !constructorRegExp.test(noop);\n\nvar isConstructorModern = function isConstructor(argument) {\n  if (!isCallable(argument)) return false;\n  try {\n    construct(noop, [], argument);\n    return true;\n  } catch (error) {\n    return false;\n  }\n};\n\nvar isConstructorLegacy = function isConstructor(argument) {\n  if (!isCallable(argument)) return false;\n  switch (classof(argument)) {\n    case 'AsyncFunction':\n    case 'GeneratorFunction':\n    case 'AsyncGeneratorFunction': return false;\n  }\n  try {\n    // we can't check .prototype since constructors produced by .bind haven't it\n    // `Function#toString` throws on some built-it function in some legacy engines\n    // (for example, `DOMQuad` and similar in FF41-)\n    return INCORRECT_TO_STRING || !!exec(constructorRegExp, inspectSource(argument));\n  } catch (error) {\n    return true;\n  }\n};\n\nisConstructorLegacy.sham = true;\n\n// `IsConstructor` abstract operation\n// https://tc39.es/ecma262/#sec-isconstructor\nmodule.exports = !construct || fails(function () {\n  var called;\n  return isConstructorModern(isConstructorModern.call)\n    || !isConstructorModern(Object)\n    || !isConstructorModern(function () { called = true; })\n    || called;\n}) ? isConstructorLegacy : isConstructorModern;\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/is-constructor.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/is-forced.js"
/*!*****************************************************!*\
  !*** ./node_modules/core-js/internals/is-forced.js ***!
  \*****************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar fails = __webpack_require__(/*! ../internals/fails */ \"./node_modules/core-js/internals/fails.js\");\nvar isCallable = __webpack_require__(/*! ../internals/is-callable */ \"./node_modules/core-js/internals/is-callable.js\");\n\nvar replacement = /#|\\.prototype\\./;\n\nvar isForced = function (feature, detection) {\n  var value = data[normalize(feature)];\n  return value === POLYFILL ? true\n    : value === NATIVE ? false\n    : isCallable(detection) ? fails(detection)\n    : !!detection;\n};\n\nvar normalize = isForced.normalize = function (string) {\n  return String(string).replace(replacement, '.').toLowerCase();\n};\n\nvar data = isForced.data = {};\nvar NATIVE = isForced.NATIVE = 'N';\nvar POLYFILL = isForced.POLYFILL = 'P';\n\nmodule.exports = isForced;\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/is-forced.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/is-null-or-undefined.js"
/*!****************************************************************!*\
  !*** ./node_modules/core-js/internals/is-null-or-undefined.js ***!
  \****************************************************************/
(module) {

eval("{\n// we can't use just `it == null` since of `document.all` special case\n// https://tc39.es/ecma262/#sec-IsHTMLDDA-internal-slot-aec\nmodule.exports = function (it) {\n  return it === null || it === undefined;\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/is-null-or-undefined.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/is-object.js"
/*!*****************************************************!*\
  !*** ./node_modules/core-js/internals/is-object.js ***!
  \*****************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar isCallable = __webpack_require__(/*! ../internals/is-callable */ \"./node_modules/core-js/internals/is-callable.js\");\n\nmodule.exports = function (it) {\n  return typeof it == 'object' ? it !== null : isCallable(it);\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/is-object.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/is-possible-prototype.js"
/*!*****************************************************************!*\
  !*** ./node_modules/core-js/internals/is-possible-prototype.js ***!
  \*****************************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar isObject = __webpack_require__(/*! ../internals/is-object */ \"./node_modules/core-js/internals/is-object.js\");\n\nmodule.exports = function (argument) {\n  return isObject(argument) || argument === null;\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/is-possible-prototype.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/is-pure.js"
/*!***************************************************!*\
  !*** ./node_modules/core-js/internals/is-pure.js ***!
  \***************************************************/
(module) {

eval("{\nmodule.exports = false;\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/is-pure.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/is-symbol.js"
/*!*****************************************************!*\
  !*** ./node_modules/core-js/internals/is-symbol.js ***!
  \*****************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar getBuiltIn = __webpack_require__(/*! ../internals/get-built-in */ \"./node_modules/core-js/internals/get-built-in.js\");\nvar isCallable = __webpack_require__(/*! ../internals/is-callable */ \"./node_modules/core-js/internals/is-callable.js\");\nvar isPrototypeOf = __webpack_require__(/*! ../internals/object-is-prototype-of */ \"./node_modules/core-js/internals/object-is-prototype-of.js\");\nvar USE_SYMBOL_AS_UID = __webpack_require__(/*! ../internals/use-symbol-as-uid */ \"./node_modules/core-js/internals/use-symbol-as-uid.js\");\n\nvar $Object = Object;\n\nmodule.exports = USE_SYMBOL_AS_UID ? function (it) {\n  return typeof it == 'symbol';\n} : function (it) {\n  var $Symbol = getBuiltIn('Symbol');\n  return isCallable($Symbol) && isPrototypeOf($Symbol.prototype, $Object(it));\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/is-symbol.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/iterate-simple.js"
/*!**********************************************************!*\
  !*** ./node_modules/core-js/internals/iterate-simple.js ***!
  \**********************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar call = __webpack_require__(/*! ../internals/function-call */ \"./node_modules/core-js/internals/function-call.js\");\n\nmodule.exports = function (record, fn, ITERATOR_INSTEAD_OF_RECORD) {\n  var iterator = ITERATOR_INSTEAD_OF_RECORD ? record : record.iterator;\n  var next = record.next;\n  var step, result;\n  while (!(step = call(next, iterator)).done) {\n    result = fn(step.value);\n    if (result !== undefined) return result;\n  }\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/iterate-simple.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/iterate.js"
/*!***************************************************!*\
  !*** ./node_modules/core-js/internals/iterate.js ***!
  \***************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar bind = __webpack_require__(/*! ../internals/function-bind-context */ \"./node_modules/core-js/internals/function-bind-context.js\");\nvar call = __webpack_require__(/*! ../internals/function-call */ \"./node_modules/core-js/internals/function-call.js\");\nvar anObject = __webpack_require__(/*! ../internals/an-object */ \"./node_modules/core-js/internals/an-object.js\");\nvar tryToString = __webpack_require__(/*! ../internals/try-to-string */ \"./node_modules/core-js/internals/try-to-string.js\");\nvar isArrayIteratorMethod = __webpack_require__(/*! ../internals/is-array-iterator-method */ \"./node_modules/core-js/internals/is-array-iterator-method.js\");\nvar lengthOfArrayLike = __webpack_require__(/*! ../internals/length-of-array-like */ \"./node_modules/core-js/internals/length-of-array-like.js\");\nvar isPrototypeOf = __webpack_require__(/*! ../internals/object-is-prototype-of */ \"./node_modules/core-js/internals/object-is-prototype-of.js\");\nvar getIterator = __webpack_require__(/*! ../internals/get-iterator */ \"./node_modules/core-js/internals/get-iterator.js\");\nvar getIteratorMethod = __webpack_require__(/*! ../internals/get-iterator-method */ \"./node_modules/core-js/internals/get-iterator-method.js\");\nvar iteratorClose = __webpack_require__(/*! ../internals/iterator-close */ \"./node_modules/core-js/internals/iterator-close.js\");\n\nvar $TypeError = TypeError;\n\nvar Result = function (stopped, result) {\n  this.stopped = stopped;\n  this.result = result;\n};\n\nvar ResultPrototype = Result.prototype;\n\nmodule.exports = function (iterable, unboundFunction, options) {\n  var that = options && options.that;\n  var AS_ENTRIES = !!(options && options.AS_ENTRIES);\n  var IS_RECORD = !!(options && options.IS_RECORD);\n  var IS_ITERATOR = !!(options && options.IS_ITERATOR);\n  var INTERRUPTED = !!(options && options.INTERRUPTED);\n  var fn = bind(unboundFunction, that);\n  var iterator, iterFn, index, length, result, next, step;\n\n  var stop = function (condition) {\n    var $iterator = iterator;\n    iterator = undefined;\n    if ($iterator) iteratorClose($iterator, 'normal');\n    return new Result(true, condition);\n  };\n\n  var callFn = function (value) {\n    if (AS_ENTRIES) {\n      anObject(value);\n      return INTERRUPTED ? fn(value[0], value[1], stop) : fn(value[0], value[1]);\n    } return INTERRUPTED ? fn(value, stop) : fn(value);\n  };\n\n  if (IS_RECORD) {\n    iterator = iterable.iterator;\n  } else if (IS_ITERATOR) {\n    iterator = iterable;\n  } else {\n    iterFn = getIteratorMethod(iterable);\n    if (!iterFn) throw new $TypeError(tryToString(iterable) + ' is not iterable');\n    // optimisation for array iterators\n    if (isArrayIteratorMethod(iterFn)) {\n      for (index = 0, length = lengthOfArrayLike(iterable); length > index; index++) {\n        result = callFn(iterable[index]);\n        if (result && isPrototypeOf(ResultPrototype, result)) return result;\n      } return new Result(false);\n    }\n    iterator = getIterator(iterable, iterFn);\n  }\n\n  next = IS_RECORD ? iterable.next : iterator.next;\n  while (!(step = call(next, iterator)).done) {\n    // `IteratorValue` errors should propagate without closing the iterator\n    var value = step.value;\n    try {\n      result = callFn(value);\n    } catch (error) {\n      if (iterator) iteratorClose(iterator, 'throw', error);\n      else throw error;\n    }\n    if (typeof result == 'object' && result && isPrototypeOf(ResultPrototype, result)) return result;\n  } return new Result(false);\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/iterate.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/iterator-close.js"
/*!**********************************************************!*\
  !*** ./node_modules/core-js/internals/iterator-close.js ***!
  \**********************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar call = __webpack_require__(/*! ../internals/function-call */ \"./node_modules/core-js/internals/function-call.js\");\nvar anObject = __webpack_require__(/*! ../internals/an-object */ \"./node_modules/core-js/internals/an-object.js\");\nvar getMethod = __webpack_require__(/*! ../internals/get-method */ \"./node_modules/core-js/internals/get-method.js\");\n\nmodule.exports = function (iterator, kind, value) {\n  var innerResult, innerError;\n  anObject(iterator);\n  try {\n    innerResult = getMethod(iterator, 'return');\n    if (!innerResult) {\n      if (kind === 'throw') throw value;\n      return value;\n    }\n    innerResult = call(innerResult, iterator);\n  } catch (error) {\n    innerError = true;\n    innerResult = error;\n  }\n  if (kind === 'throw') throw value;\n  if (innerError) throw innerResult;\n  anObject(innerResult);\n  return value;\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/iterator-close.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/iterator-create-constructor.js"
/*!***********************************************************************!*\
  !*** ./node_modules/core-js/internals/iterator-create-constructor.js ***!
  \***********************************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar IteratorPrototype = (__webpack_require__(/*! ../internals/iterators-core */ \"./node_modules/core-js/internals/iterators-core.js\").IteratorPrototype);\nvar create = __webpack_require__(/*! ../internals/object-create */ \"./node_modules/core-js/internals/object-create.js\");\nvar createPropertyDescriptor = __webpack_require__(/*! ../internals/create-property-descriptor */ \"./node_modules/core-js/internals/create-property-descriptor.js\");\nvar setToStringTag = __webpack_require__(/*! ../internals/set-to-string-tag */ \"./node_modules/core-js/internals/set-to-string-tag.js\");\nvar Iterators = __webpack_require__(/*! ../internals/iterators */ \"./node_modules/core-js/internals/iterators.js\");\n\nvar returnThis = function () { return this; };\n\nmodule.exports = function (IteratorConstructor, NAME, next, ENUMERABLE_NEXT) {\n  var TO_STRING_TAG = NAME + ' Iterator';\n  IteratorConstructor.prototype = create(IteratorPrototype, { next: createPropertyDescriptor(+!ENUMERABLE_NEXT, next) });\n  setToStringTag(IteratorConstructor, TO_STRING_TAG, false, true);\n  Iterators[TO_STRING_TAG] = returnThis;\n  return IteratorConstructor;\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/iterator-create-constructor.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/iterator-define.js"
/*!***********************************************************!*\
  !*** ./node_modules/core-js/internals/iterator-define.js ***!
  \***********************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar $ = __webpack_require__(/*! ../internals/export */ \"./node_modules/core-js/internals/export.js\");\nvar call = __webpack_require__(/*! ../internals/function-call */ \"./node_modules/core-js/internals/function-call.js\");\nvar IS_PURE = __webpack_require__(/*! ../internals/is-pure */ \"./node_modules/core-js/internals/is-pure.js\");\nvar FunctionName = __webpack_require__(/*! ../internals/function-name */ \"./node_modules/core-js/internals/function-name.js\");\nvar isCallable = __webpack_require__(/*! ../internals/is-callable */ \"./node_modules/core-js/internals/is-callable.js\");\nvar createIteratorConstructor = __webpack_require__(/*! ../internals/iterator-create-constructor */ \"./node_modules/core-js/internals/iterator-create-constructor.js\");\nvar getPrototypeOf = __webpack_require__(/*! ../internals/object-get-prototype-of */ \"./node_modules/core-js/internals/object-get-prototype-of.js\");\nvar setPrototypeOf = __webpack_require__(/*! ../internals/object-set-prototype-of */ \"./node_modules/core-js/internals/object-set-prototype-of.js\");\nvar setToStringTag = __webpack_require__(/*! ../internals/set-to-string-tag */ \"./node_modules/core-js/internals/set-to-string-tag.js\");\nvar createNonEnumerableProperty = __webpack_require__(/*! ../internals/create-non-enumerable-property */ \"./node_modules/core-js/internals/create-non-enumerable-property.js\");\nvar defineBuiltIn = __webpack_require__(/*! ../internals/define-built-in */ \"./node_modules/core-js/internals/define-built-in.js\");\nvar wellKnownSymbol = __webpack_require__(/*! ../internals/well-known-symbol */ \"./node_modules/core-js/internals/well-known-symbol.js\");\nvar Iterators = __webpack_require__(/*! ../internals/iterators */ \"./node_modules/core-js/internals/iterators.js\");\nvar IteratorsCore = __webpack_require__(/*! ../internals/iterators-core */ \"./node_modules/core-js/internals/iterators-core.js\");\n\nvar PROPER_FUNCTION_NAME = FunctionName.PROPER;\nvar CONFIGURABLE_FUNCTION_NAME = FunctionName.CONFIGURABLE;\nvar IteratorPrototype = IteratorsCore.IteratorPrototype;\nvar BUGGY_SAFARI_ITERATORS = IteratorsCore.BUGGY_SAFARI_ITERATORS;\nvar ITERATOR = wellKnownSymbol('iterator');\nvar KEYS = 'keys';\nvar VALUES = 'values';\nvar ENTRIES = 'entries';\n\nvar returnThis = function () { return this; };\n\nmodule.exports = function (Iterable, NAME, IteratorConstructor, next, DEFAULT, IS_SET, FORCED) {\n  createIteratorConstructor(IteratorConstructor, NAME, next);\n\n  var getIterationMethod = function (KIND) {\n    if (KIND === DEFAULT && defaultIterator) return defaultIterator;\n    if (!BUGGY_SAFARI_ITERATORS && KIND && KIND in IterablePrototype) return IterablePrototype[KIND];\n\n    switch (KIND) {\n      case KEYS: return function keys() { return new IteratorConstructor(this, KIND); };\n      case VALUES: return function values() { return new IteratorConstructor(this, KIND); };\n      case ENTRIES: return function entries() { return new IteratorConstructor(this, KIND); };\n    }\n\n    return function () { return new IteratorConstructor(this); };\n  };\n\n  var TO_STRING_TAG = NAME + ' Iterator';\n  var INCORRECT_VALUES_NAME = false;\n  var IterablePrototype = Iterable.prototype;\n  var nativeIterator = IterablePrototype[ITERATOR]\n    || IterablePrototype['@@iterator']\n    || DEFAULT && IterablePrototype[DEFAULT];\n  var defaultIterator = !BUGGY_SAFARI_ITERATORS && nativeIterator || getIterationMethod(DEFAULT);\n  var anyNativeIterator = NAME === 'Array' ? IterablePrototype.entries || nativeIterator : nativeIterator;\n  var CurrentIteratorPrototype, methods, KEY;\n\n  // fix native\n  if (anyNativeIterator) {\n    CurrentIteratorPrototype = getPrototypeOf(anyNativeIterator.call(new Iterable()));\n    if (CurrentIteratorPrototype !== Object.prototype && CurrentIteratorPrototype.next) {\n      if (!IS_PURE && getPrototypeOf(CurrentIteratorPrototype) !== IteratorPrototype) {\n        if (setPrototypeOf) {\n          setPrototypeOf(CurrentIteratorPrototype, IteratorPrototype);\n        } else if (!isCallable(CurrentIteratorPrototype[ITERATOR])) {\n          defineBuiltIn(CurrentIteratorPrototype, ITERATOR, returnThis);\n        }\n      }\n      // Set @@toStringTag to native iterators\n      setToStringTag(CurrentIteratorPrototype, TO_STRING_TAG, true, true);\n      if (IS_PURE) Iterators[TO_STRING_TAG] = returnThis;\n    }\n  }\n\n  // fix Array.prototype.{ values, @@iterator }.name in V8 / FF\n  if (PROPER_FUNCTION_NAME && DEFAULT === VALUES && nativeIterator && nativeIterator.name !== VALUES) {\n    if (!IS_PURE && CONFIGURABLE_FUNCTION_NAME) {\n      createNonEnumerableProperty(IterablePrototype, 'name', VALUES);\n    } else {\n      INCORRECT_VALUES_NAME = true;\n      defaultIterator = function values() { return call(nativeIterator, this); };\n    }\n  }\n\n  // export additional methods\n  if (DEFAULT) {\n    methods = {\n      values: getIterationMethod(VALUES),\n      keys: IS_SET ? defaultIterator : getIterationMethod(KEYS),\n      entries: getIterationMethod(ENTRIES)\n    };\n    if (FORCED) for (KEY in methods) {\n      if (BUGGY_SAFARI_ITERATORS || INCORRECT_VALUES_NAME || !(KEY in IterablePrototype)) {\n        defineBuiltIn(IterablePrototype, KEY, methods[KEY]);\n      }\n    } else $({ target: NAME, proto: true, forced: BUGGY_SAFARI_ITERATORS || INCORRECT_VALUES_NAME }, methods);\n  }\n\n  // define iterator\n  if ((!IS_PURE || FORCED) && IterablePrototype[ITERATOR] !== defaultIterator) {\n    defineBuiltIn(IterablePrototype, ITERATOR, defaultIterator, { name: DEFAULT });\n  }\n  Iterators[NAME] = defaultIterator;\n\n  return methods;\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/iterator-define.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/iterators-core.js"
/*!**********************************************************!*\
  !*** ./node_modules/core-js/internals/iterators-core.js ***!
  \**********************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar fails = __webpack_require__(/*! ../internals/fails */ \"./node_modules/core-js/internals/fails.js\");\nvar isCallable = __webpack_require__(/*! ../internals/is-callable */ \"./node_modules/core-js/internals/is-callable.js\");\nvar isObject = __webpack_require__(/*! ../internals/is-object */ \"./node_modules/core-js/internals/is-object.js\");\nvar create = __webpack_require__(/*! ../internals/object-create */ \"./node_modules/core-js/internals/object-create.js\");\nvar getPrototypeOf = __webpack_require__(/*! ../internals/object-get-prototype-of */ \"./node_modules/core-js/internals/object-get-prototype-of.js\");\nvar defineBuiltIn = __webpack_require__(/*! ../internals/define-built-in */ \"./node_modules/core-js/internals/define-built-in.js\");\nvar wellKnownSymbol = __webpack_require__(/*! ../internals/well-known-symbol */ \"./node_modules/core-js/internals/well-known-symbol.js\");\nvar IS_PURE = __webpack_require__(/*! ../internals/is-pure */ \"./node_modules/core-js/internals/is-pure.js\");\n\nvar ITERATOR = wellKnownSymbol('iterator');\nvar BUGGY_SAFARI_ITERATORS = false;\n\n// `%IteratorPrototype%` object\n// https://tc39.es/ecma262/#sec-%iteratorprototype%-object\nvar IteratorPrototype, PrototypeOfArrayIteratorPrototype, arrayIterator;\n\n/* eslint-disable es/no-array-prototype-keys -- safe */\nif ([].keys) {\n  arrayIterator = [].keys();\n  // Safari 8 has buggy iterators w/o `next`\n  if (!('next' in arrayIterator)) BUGGY_SAFARI_ITERATORS = true;\n  else {\n    PrototypeOfArrayIteratorPrototype = getPrototypeOf(getPrototypeOf(arrayIterator));\n    if (PrototypeOfArrayIteratorPrototype !== Object.prototype) IteratorPrototype = PrototypeOfArrayIteratorPrototype;\n  }\n}\n\nvar NEW_ITERATOR_PROTOTYPE = !isObject(IteratorPrototype) || fails(function () {\n  var test = {};\n  // FF44- legacy iterators case\n  return IteratorPrototype[ITERATOR].call(test) !== test;\n});\n\nif (NEW_ITERATOR_PROTOTYPE) IteratorPrototype = {};\nelse if (IS_PURE) IteratorPrototype = create(IteratorPrototype);\n\n// `%IteratorPrototype%[@@iterator]()` method\n// https://tc39.es/ecma262/#sec-%iteratorprototype%-@@iterator\nif (!isCallable(IteratorPrototype[ITERATOR])) {\n  defineBuiltIn(IteratorPrototype, ITERATOR, function () {\n    return this;\n  });\n}\n\nmodule.exports = {\n  IteratorPrototype: IteratorPrototype,\n  BUGGY_SAFARI_ITERATORS: BUGGY_SAFARI_ITERATORS\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/iterators-core.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/iterators.js"
/*!*****************************************************!*\
  !*** ./node_modules/core-js/internals/iterators.js ***!
  \*****************************************************/
(module) {

eval("{\nmodule.exports = {};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/iterators.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/length-of-array-like.js"
/*!****************************************************************!*\
  !*** ./node_modules/core-js/internals/length-of-array-like.js ***!
  \****************************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar toLength = __webpack_require__(/*! ../internals/to-length */ \"./node_modules/core-js/internals/to-length.js\");\n\n// `LengthOfArrayLike` abstract operation\n// https://tc39.es/ecma262/#sec-lengthofarraylike\nmodule.exports = function (obj) {\n  return toLength(obj.length);\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/length-of-array-like.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/make-built-in.js"
/*!*********************************************************!*\
  !*** ./node_modules/core-js/internals/make-built-in.js ***!
  \*********************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar uncurryThis = __webpack_require__(/*! ../internals/function-uncurry-this */ \"./node_modules/core-js/internals/function-uncurry-this.js\");\nvar fails = __webpack_require__(/*! ../internals/fails */ \"./node_modules/core-js/internals/fails.js\");\nvar isCallable = __webpack_require__(/*! ../internals/is-callable */ \"./node_modules/core-js/internals/is-callable.js\");\nvar hasOwn = __webpack_require__(/*! ../internals/has-own-property */ \"./node_modules/core-js/internals/has-own-property.js\");\nvar DESCRipTORS = __webpack_require__(/*! ../internals/descriptors */ \"./node_modules/core-js/internals/descriptors.js\");\nvar CONFIGURABLE_FUNCTION_NAME = (__webpack_require__(/*! ../internals/function-name */ \"./node_modules/core-js/internals/function-name.js\").CONFIGURABLE);\nvar inspectSource = __webpack_require__(/*! ../internals/inspect-source */ \"./node_modules/core-js/internals/inspect-source.js\");\nvar InternalStateModule = __webpack_require__(/*! ../internals/internal-state */ \"./node_modules/core-js/internals/internal-state.js\");\n\nvar enforceInternalState = InternalStateModule.enforce;\nvar getInternalState = InternalStateModule.get;\nvar $String = String;\n// eslint-disable-next-line es/no-object-defineproperty -- safe\nvar defineProperty = Object.defineProperty;\nvar stringSlice = uncurryThis(''.slice);\nvar replace = uncurryThis(''.replace);\nvar join = uncurryThis([].join);\n\nvar CONFIGURABLE_LENGTH = DESCRipTORS && !fails(function () {\n  return defineProperty(function () { /* empty */ }, 'length', { value: 8 }).length !== 8;\n});\n\nvar TEMPLATE = String(String).split('String');\n\nvar makeBuiltIn = module.exports = function (value, name, options) {\n  if (stringSlice($String(name), 0, 7) === 'Symbol(') {\n    name = '[' + replace($String(name), /^Symbol\\(([^)]*)\\).*$/, '$1') + ']';\n  }\n  if (options && options.getter) name = 'get ' + name;\n  if (options && options.setter) name = 'set ' + name;\n  if (!hasOwn(value, 'name') || (CONFIGURABLE_FUNCTION_NAME && value.name !== name)) {\n    if (DESCRipTORS) defineProperty(value, 'name', { value: name, configurable: true });\n    else value.name = name;\n  }\n  if (CONFIGURABLE_LENGTH && options && hasOwn(options, 'arity') && value.length !== options.arity) {\n    defineProperty(value, 'length', { value: options.arity });\n  }\n  try {\n    if (options && hasOwn(options, 'constructor') && options.constructor) {\n      if (DESCRipTORS) defineProperty(value, 'prototype', { writable: false });\n    // in V8 ~ Chrome 53, prototypes of some methods, like `Array.prototype.values`, are non-writable\n    } else if (value.prototype) value.prototype = undefined;\n  } catch (error) { /* empty */ }\n  var state = enforceInternalState(value);\n  if (!hasOwn(state, 'source')) {\n    state.source = join(TEMPLATE, typeof name == 'string' ? name : '');\n  } return value;\n};\n\n// add fake Function#toString for correct work wrapped methods / constructors with methods like LoDash isNative\n// eslint-disable-next-line no-extend-native -- required\nFunction.prototype.toString = makeBuiltIn(function toString() {\n  return isCallable(this) && getInternalState(this).source || inspectSource(this);\n}, 'toString');\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/make-built-in.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/map-helpers.js"
/*!*******************************************************!*\
  !*** ./node_modules/core-js/internals/map-helpers.js ***!
  \*******************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar uncurryThis = __webpack_require__(/*! ../internals/function-uncurry-this */ \"./node_modules/core-js/internals/function-uncurry-this.js\");\n\n// eslint-disable-next-line es/no-map -- safe\nvar MapPrototype = Map.prototype;\n\nmodule.exports = {\n  // eslint-disable-next-line es/no-map -- safe\n  Map: Map,\n  set: uncurryThis(MapPrototype.set),\n  get: uncurryThis(MapPrototype.get),\n  has: uncurryThis(MapPrototype.has),\n  remove: uncurryThis(MapPrototype['delete']),\n  proto: MapPrototype\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/map-helpers.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/math-trunc.js"
/*!******************************************************!*\
  !*** ./node_modules/core-js/internals/math-trunc.js ***!
  \******************************************************/
(module) {

eval("{\nvar ceil = Math.ceil;\nvar floor = Math.floor;\n\n// `Math.trunc` method\n// https://tc39.es/ecma262/#sec-math.trunc\n// eslint-disable-next-line es/no-math-trunc -- safe\nmodule.exports = Math.trunc || function trunc(x) {\n  var n = +x;\n  return (n > 0 ? floor : ceil)(n);\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/math-trunc.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/normalize-string-argument.js"
/*!*********************************************************************!*\
  !*** ./node_modules/core-js/internals/normalize-string-argument.js ***!
  \*********************************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar toString = __webpack_require__(/*! ../internals/to-string */ \"./node_modules/core-js/internals/to-string.js\");\n\nmodule.exports = function (argument, $default) {\n  return argument === undefined ? arguments.length < 2 ? '' : $default : toString(argument);\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/normalize-string-argument.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/object-create.js"
/*!*********************************************************!*\
  !*** ./node_modules/core-js/internals/object-create.js ***!
  \*********************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\n/* global ActiveXObject -- old IE, WSH */\nvar anObject = __webpack_require__(/*! ../internals/an-object */ \"./node_modules/core-js/internals/an-object.js\");\nvar definePropertiesModule = __webpack_require__(/*! ../internals/object-define-properties */ \"./node_modules/core-js/internals/object-define-properties.js\");\nvar enumBugKeys = __webpack_require__(/*! ../internals/enum-bug-keys */ \"./node_modules/core-js/internals/enum-bug-keys.js\");\nvar hiddenKeys = __webpack_require__(/*! ../internals/hidden-keys */ \"./node_modules/core-js/internals/hidden-keys.js\");\nvar html = __webpack_require__(/*! ../internals/html */ \"./node_modules/core-js/internals/html.js\");\nvar documentCreateElement = __webpack_require__(/*! ../internals/document-create-element */ \"./node_modules/core-js/internals/document-create-element.js\");\nvar sharedKey = __webpack_require__(/*! ../internals/shared-key */ \"./node_modules/core-js/internals/shared-key.js\");\n\nvar GT = '>';\nvar LT = '<';\nvar PROTOTYPE = 'prototype';\nvar SCRipT = 'script';\nvar IE_PROTO = sharedKey('IE_PROTO');\n\nvar EmptyConstructor = function () { /* empty */ };\n\nvar scriptTag = function (content) {\n  return LT + SCRipT + GT + content + LT + '/' + SCRipT + GT;\n};\n\n// Create object with fake `null` prototype: use ActiveX Object with cleared prototype\nvar NullProtoObjectViaActiveX = function (activeXDocument) {\n  activeXDocument.write(scriptTag(''));\n  activeXDocument.close();\n  var temp = activeXDocument.parentWindow.Object;\n  // eslint-disable-next-line no-useless-assignment -- avoid memory leak\n  activeXDocument = null;\n  return temp;\n};\n\n// Create object with fake `null` prototype: use iframe Object with cleared prototype\nvar NullProtoObjectViaIFrame = function () {\n  // Thrash, waste and sodomy: IE GC bug\n  var iframe = documentCreateElement('iframe');\n  var JS = 'java' + SCRipT + ':';\n  var iframeDocument;\n  iframe.style.display = 'none';\n  html.appendChild(iframe);\n  // https://github.com/zloirock/core-js/issues/475\n  iframe.src = String(JS);\n  iframeDocument = iframe.contentWindow.document;\n  iframeDocument.open();\n  iframeDocument.write(scriptTag('document.F=Object'));\n  iframeDocument.close();\n  return iframeDocument.F;\n};\n\n// Check for document.domain and active x support\n// No need to use active x approach when document.domain is not set\n// see https://github.com/es-shims/es5-shim/issues/150\n// variation of https://github.com/kitcambridge/es5-shim/commit/4f738ac066346\n// avoid IE GC bug\nvar activeXDocument;\nvar NullProtoObject = function () {\n  try {\n    activeXDocument = new ActiveXObject('htmlfile');\n  } catch (error) { /* ignore */ }\n  NullProtoObject = typeof document != 'undefined'\n    ? document.domain && activeXDocument\n      ? NullProtoObjectViaActiveX(activeXDocument) // old IE\n      : NullProtoObjectViaIFrame()\n    : NullProtoObjectViaActiveX(activeXDocument); // WSH\n  var length = enumBugKeys.length;\n  while (length--) delete NullProtoObject[PROTOTYPE][enumBugKeys[length]];\n  return NullProtoObject();\n};\n\nhiddenKeys[IE_PROTO] = true;\n\n// `Object.create` method\n// https://tc39.es/ecma262/#sec-object.create\n// eslint-disable-next-line es/no-object-create -- safe\nmodule.exports = Object.create || function create(O, Properties) {\n  var result;\n  if (O !== null) {\n    EmptyConstructor[PROTOTYPE] = anObject(O);\n    result = new EmptyConstructor();\n    EmptyConstructor[PROTOTYPE] = null;\n    // add \"__proto__\" for Object.getPrototypeOf polyfill\n    result[IE_PROTO] = O;\n  } else result = NullProtoObject();\n  return Properties === undefined ? result : definePropertiesModule.f(result, Properties);\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/object-create.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/object-define-properties.js"
/*!********************************************************************!*\
  !*** ./node_modules/core-js/internals/object-define-properties.js ***!
  \********************************************************************/
(__unused_webpack_module, exports, __webpack_require__) {

eval("{\nvar DESCRipTORS = __webpack_require__(/*! ../internals/descriptors */ \"./node_modules/core-js/internals/descriptors.js\");\nvar V8_PROTOTYPE_DEFINE_BUG = __webpack_require__(/*! ../internals/v8-prototype-define-bug */ \"./node_modules/core-js/internals/v8-prototype-define-bug.js\");\nvar definePropertyModule = __webpack_require__(/*! ../internals/object-define-property */ \"./node_modules/core-js/internals/object-define-property.js\");\nvar anObject = __webpack_require__(/*! ../internals/an-object */ \"./node_modules/core-js/internals/an-object.js\");\nvar toIndexedObject = __webpack_require__(/*! ../internals/to-indexed-object */ \"./node_modules/core-js/internals/to-indexed-object.js\");\nvar objectKeys = __webpack_require__(/*! ../internals/object-keys */ \"./node_modules/core-js/internals/object-keys.js\");\n\n// `Object.defineProperties` method\n// https://tc39.es/ecma262/#sec-object.defineproperties\n// eslint-disable-next-line es/no-object-defineproperties -- safe\nexports.f = DESCRipTORS && !V8_PROTOTYPE_DEFINE_BUG ? Object.defineProperties : function defineProperties(O, Properties) {\n  anObject(O);\n  var props = toIndexedObject(Properties);\n  var keys = objectKeys(Properties);\n  var length = keys.length;\n  var index = 0;\n  var key;\n  while (length > index) definePropertyModule.f(O, key = keys[index++], props[key]);\n  return O;\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/object-define-properties.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/object-define-property.js"
/*!******************************************************************!*\
  !*** ./node_modules/core-js/internals/object-define-property.js ***!
  \******************************************************************/
(__unused_webpack_module, exports, __webpack_require__) {

eval("{\nvar DESCRipTORS = __webpack_require__(/*! ../internals/descriptors */ \"./node_modules/core-js/internals/descriptors.js\");\nvar IE8_DOM_DEFINE = __webpack_require__(/*! ../internals/ie8-dom-define */ \"./node_modules/core-js/internals/ie8-dom-define.js\");\nvar V8_PROTOTYPE_DEFINE_BUG = __webpack_require__(/*! ../internals/v8-prototype-define-bug */ \"./node_modules/core-js/internals/v8-prototype-define-bug.js\");\nvar anObject = __webpack_require__(/*! ../internals/an-object */ \"./node_modules/core-js/internals/an-object.js\");\nvar toPropertyKey = __webpack_require__(/*! ../internals/to-property-key */ \"./node_modules/core-js/internals/to-property-key.js\");\n\nvar $TypeError = TypeError;\n// eslint-disable-next-line es/no-object-defineproperty -- safe\nvar $defineProperty = Object.defineProperty;\n// eslint-disable-next-line es/no-object-getownpropertydescriptor -- safe\nvar $getOwnPropertyDescriptor = Object.getOwnPropertyDescriptor;\nvar ENUMERABLE = 'enumerable';\nvar CONFIGURABLE = 'configurable';\nvar WRITABLE = 'writable';\n\n// `Object.defineProperty` method\n// https://tc39.es/ecma262/#sec-object.defineproperty\nexports.f = DESCRipTORS ? V8_PROTOTYPE_DEFINE_BUG ? function defineProperty(O, P, Attributes) {\n  anObject(O);\n  P = toPropertyKey(P);\n  anObject(Attributes);\n  if (typeof O === 'function' && P === 'prototype' && 'value' in Attributes && WRITABLE in Attributes && !Attributes[WRITABLE]) {\n    var current = $getOwnPropertyDescriptor(O, P);\n    if (current && current[WRITABLE]) {\n      O[P] = Attributes.value;\n      Attributes = {\n        configurable: CONFIGURABLE in Attributes ? Attributes[CONFIGURABLE] : current[CONFIGURABLE],\n        enumerable: ENUMERABLE in Attributes ? Attributes[ENUMERABLE] : current[ENUMERABLE],\n        writable: false\n      };\n    }\n  } return $defineProperty(O, P, Attributes);\n} : $defineProperty : function defineProperty(O, P, Attributes) {\n  anObject(O);\n  P = toPropertyKey(P);\n  anObject(Attributes);\n  if (IE8_DOM_DEFINE) try {\n    return $defineProperty(O, P, Attributes);\n  } catch (error) { /* empty */ }\n  if ('get' in Attributes || 'set' in Attributes) throw new $TypeError('Accessors not supported');\n  if ('value' in Attributes) O[P] = Attributes.value;\n  return O;\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/object-define-property.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/object-get-own-property-descriptor.js"
/*!******************************************************************************!*\
  !*** ./node_modules/core-js/internals/object-get-own-property-descriptor.js ***!
  \******************************************************************************/
(__unused_webpack_module, exports, __webpack_require__) {

eval("{\nvar DESCRipTORS = __webpack_require__(/*! ../internals/descriptors */ \"./node_modules/core-js/internals/descriptors.js\");\nvar call = __webpack_require__(/*! ../internals/function-call */ \"./node_modules/core-js/internals/function-call.js\");\nvar propertyIsEnumerableModule = __webpack_require__(/*! ../internals/object-property-is-enumerable */ \"./node_modules/core-js/internals/object-property-is-enumerable.js\");\nvar createPropertyDescriptor = __webpack_require__(/*! ../internals/create-property-descriptor */ \"./node_modules/core-js/internals/create-property-descriptor.js\");\nvar toIndexedObject = __webpack_require__(/*! ../internals/to-indexed-object */ \"./node_modules/core-js/internals/to-indexed-object.js\");\nvar toPropertyKey = __webpack_require__(/*! ../internals/to-property-key */ \"./node_modules/core-js/internals/to-property-key.js\");\nvar hasOwn = __webpack_require__(/*! ../internals/has-own-property */ \"./node_modules/core-js/internals/has-own-property.js\");\nvar IE8_DOM_DEFINE = __webpack_require__(/*! ../internals/ie8-dom-define */ \"./node_modules/core-js/internals/ie8-dom-define.js\");\n\n// eslint-disable-next-line es/no-object-getownpropertydescriptor -- safe\nvar $getOwnPropertyDescriptor = Object.getOwnPropertyDescriptor;\n\n// `Object.getOwnPropertyDescriptor` method\n// https://tc39.es/ecma262/#sec-object.getownpropertydescriptor\nexports.f = DESCRipTORS ? $getOwnPropertyDescriptor : function getOwnPropertyDescriptor(O, P) {\n  O = toIndexedObject(O);\n  P = toPropertyKey(P);\n  if (IE8_DOM_DEFINE) try {\n    return $getOwnPropertyDescriptor(O, P);\n  } catch (error) { /* empty */ }\n  if (hasOwn(O, P)) return createPropertyDescriptor(!call(propertyIsEnumerableModule.f, O, P), O[P]);\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/object-get-own-property-descriptor.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/object-get-own-property-names-external.js"
/*!**********************************************************************************!*\
  !*** ./node_modules/core-js/internals/object-get-own-property-names-external.js ***!
  \**********************************************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\n/* eslint-disable es/no-object-getownpropertynames -- safe */\nvar classof = __webpack_require__(/*! ../internals/classof-raw */ \"./node_modules/core-js/internals/classof-raw.js\");\nvar toIndexedObject = __webpack_require__(/*! ../internals/to-indexed-object */ \"./node_modules/core-js/internals/to-indexed-object.js\");\nvar $getOwnPropertyNames = (__webpack_require__(/*! ../internals/object-get-own-property-names */ \"./node_modules/core-js/internals/object-get-own-property-names.js\").f);\nvar arraySlice = __webpack_require__(/*! ../internals/array-slice */ \"./node_modules/core-js/internals/array-slice.js\");\n\nvar windowNames = typeof window == 'object' && window && Object.getOwnPropertyNames\n  ? Object.getOwnPropertyNames(window) : [];\n\nvar getWindowNames = function (it) {\n  try {\n    return $getOwnPropertyNames(it);\n  } catch (error) {\n    return arraySlice(windowNames);\n  }\n};\n\n// fallback for IE11 buggy Object.getOwnPropertyNames with iframe and window\nmodule.exports.f = function getOwnPropertyNames(it) {\n  return windowNames && classof(it) === 'Window'\n    ? getWindowNames(it)\n    : $getOwnPropertyNames(toIndexedObject(it));\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/object-get-own-property-names-external.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/object-get-own-property-names.js"
/*!*************************************************************************!*\
  !*** ./node_modules/core-js/internals/object-get-own-property-names.js ***!
  \*************************************************************************/
(__unused_webpack_module, exports, __webpack_require__) {

eval("{\nvar internalObjectKeys = __webpack_require__(/*! ../internals/object-keys-internal */ \"./node_modules/core-js/internals/object-keys-internal.js\");\nvar enumBugKeys = __webpack_require__(/*! ../internals/enum-bug-keys */ \"./node_modules/core-js/internals/enum-bug-keys.js\");\n\nvar hiddenKeys = enumBugKeys.concat('length', 'prototype');\n\n// `Object.getOwnPropertyNames` method\n// https://tc39.es/ecma262/#sec-object.getownpropertynames\n// eslint-disable-next-line es/no-object-getownpropertynames -- safe\nexports.f = Object.getOwnPropertyNames || function getOwnPropertyNames(O) {\n  return internalObjectKeys(O, hiddenKeys);\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/object-get-own-property-names.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/object-get-own-property-symbols.js"
/*!***************************************************************************!*\
  !*** ./node_modules/core-js/internals/object-get-own-property-symbols.js ***!
  \***************************************************************************/
(__unused_webpack_module, exports) {

eval("{\n// eslint-disable-next-line es/no-object-getownpropertysymbols -- safe\nexports.f = Object.getOwnPropertySymbols;\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/object-get-own-property-symbols.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/object-get-prototype-of.js"
/*!*******************************************************************!*\
  !*** ./node_modules/core-js/internals/object-get-prototype-of.js ***!
  \*******************************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar hasOwn = __webpack_require__(/*! ../internals/has-own-property */ \"./node_modules/core-js/internals/has-own-property.js\");\nvar isCallable = __webpack_require__(/*! ../internals/is-callable */ \"./node_modules/core-js/internals/is-callable.js\");\nvar toObject = __webpack_require__(/*! ../internals/to-object */ \"./node_modules/core-js/internals/to-object.js\");\nvar sharedKey = __webpack_require__(/*! ../internals/shared-key */ \"./node_modules/core-js/internals/shared-key.js\");\nvar CORRECT_PROTOTYPE_GETTER = __webpack_require__(/*! ../internals/correct-prototype-getter */ \"./node_modules/core-js/internals/correct-prototype-getter.js\");\n\nvar IE_PROTO = sharedKey('IE_PROTO');\nvar $Object = Object;\nvar ObjectPrototype = $Object.prototype;\n\n// `Object.getPrototypeOf` method\n// https://tc39.es/ecma262/#sec-object.getprototypeof\n// eslint-disable-next-line es/no-object-getprototypeof -- safe\nmodule.exports = CORRECT_PROTOTYPE_GETTER ? $Object.getPrototypeOf : function (O) {\n  var object = toObject(O);\n  if (hasOwn(object, IE_PROTO)) return object[IE_PROTO];\n  var constructor = object.constructor;\n  if (isCallable(constructor) && object instanceof constructor) {\n    return constructor.prototype;\n  } return object instanceof $Object ? ObjectPrototype : null;\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/object-get-prototype-of.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/object-is-extensible.js"
/*!****************************************************************!*\
  !*** ./node_modules/core-js/internals/object-is-extensible.js ***!
  \****************************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar fails = __webpack_require__(/*! ../internals/fails */ \"./node_modules/core-js/internals/fails.js\");\nvar isObject = __webpack_require__(/*! ../internals/is-object */ \"./node_modules/core-js/internals/is-object.js\");\nvar classof = __webpack_require__(/*! ../internals/classof-raw */ \"./node_modules/core-js/internals/classof-raw.js\");\nvar ARRAY_BUFFER_NON_EXTENSIBLE = __webpack_require__(/*! ../internals/array-buffer-non-extensible */ \"./node_modules/core-js/internals/array-buffer-non-extensible.js\");\n\n// eslint-disable-next-line es/no-object-isextensible -- safe\nvar $isExtensible = Object.isExtensible;\nvar FAILS_ON_PRIMITIVES = fails(function () { $isExtensible(1); });\n\n// `Object.isExtensible` method\n// https://tc39.es/ecma262/#sec-object.isextensible\nmodule.exports = (FAILS_ON_PRIMITIVES || ARRAY_BUFFER_NON_EXTENSIBLE) ? function isExtensible(it) {\n  if (!isObject(it)) return false;\n  if (ARRAY_BUFFER_NON_EXTENSIBLE && classof(it) === 'ArrayBuffer') return false;\n  return $isExtensible ? $isExtensible(it) : true;\n} : $isExtensible;\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/object-is-extensible.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/object-is-prototype-of.js"
/*!******************************************************************!*\
  !*** ./node_modules/core-js/internals/object-is-prototype-of.js ***!
  \******************************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar uncurryThis = __webpack_require__(/*! ../internals/function-uncurry-this */ \"./node_modules/core-js/internals/function-uncurry-this.js\");\n\nmodule.exports = uncurryThis({}.isPrototypeOf);\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/object-is-prototype-of.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/object-keys-internal.js"
/*!****************************************************************!*\
  !*** ./node_modules/core-js/internals/object-keys-internal.js ***!
  \****************************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar uncurryThis = __webpack_require__(/*! ../internals/function-uncurry-this */ \"./node_modules/core-js/internals/function-uncurry-this.js\");\nvar hasOwn = __webpack_require__(/*! ../internals/has-own-property */ \"./node_modules/core-js/internals/has-own-property.js\");\nvar toIndexedObject = __webpack_require__(/*! ../internals/to-indexed-object */ \"./node_modules/core-js/internals/to-indexed-object.js\");\nvar indexOf = (__webpack_require__(/*! ../internals/array-includes */ \"./node_modules/core-js/internals/array-includes.js\").indexOf);\nvar hiddenKeys = __webpack_require__(/*! ../internals/hidden-keys */ \"./node_modules/core-js/internals/hidden-keys.js\");\n\nvar push = uncurryThis([].push);\n\nmodule.exports = function (object, names) {\n  var O = toIndexedObject(object);\n  var i = 0;\n  var result = [];\n  var key;\n  for (key in O) !hasOwn(hiddenKeys, key) && hasOwn(O, key) && push(result, key);\n  // Don't enum bug & hidden keys\n  while (names.length > i) if (hasOwn(O, key = names[i++])) {\n    ~indexOf(result, key) || push(result, key);\n  }\n  return result;\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/object-keys-internal.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/object-keys.js"
/*!*******************************************************!*\
  !*** ./node_modules/core-js/internals/object-keys.js ***!
  \*******************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar internalObjectKeys = __webpack_require__(/*! ../internals/object-keys-internal */ \"./node_modules/core-js/internals/object-keys-internal.js\");\nvar enumBugKeys = __webpack_require__(/*! ../internals/enum-bug-keys */ \"./node_modules/core-js/internals/enum-bug-keys.js\");\n\n// `Object.keys` method\n// https://tc39.es/ecma262/#sec-object.keys\n// eslint-disable-next-line es/no-object-keys -- safe\nmodule.exports = Object.keys || function keys(O) {\n  return internalObjectKeys(O, enumBugKeys);\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/object-keys.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/object-property-is-enumerable.js"
/*!*************************************************************************!*\
  !*** ./node_modules/core-js/internals/object-property-is-enumerable.js ***!
  \*************************************************************************/
(__unused_webpack_module, exports) {

eval("{\nvar $propertyIsEnumerable = {}.propertyIsEnumerable;\n// eslint-disable-next-line es/no-object-getownpropertydescriptor -- safe\nvar getOwnPropertyDescriptor = Object.getOwnPropertyDescriptor;\n\n// Nashorn ~ JDK8 bug\nvar NASHORN_BUG = getOwnPropertyDescriptor && !$propertyIsEnumerable.call({ 1: 2 }, 1);\n\n// `Object.prototype.propertyIsEnumerable` method implementation\n// https://tc39.es/ecma262/#sec-object.prototype.propertyisenumerable\nexports.f = NASHORN_BUG ? function propertyIsEnumerable(V) {\n  var descriptor = getOwnPropertyDescriptor(this, V);\n  return !!descriptor && descriptor.enumerable;\n} : $propertyIsEnumerable;\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/object-property-is-enumerable.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/object-set-prototype-of.js"
/*!*******************************************************************!*\
  !*** ./node_modules/core-js/internals/object-set-prototype-of.js ***!
  \*******************************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\n/* eslint-disable no-proto -- safe */\nvar uncurryThisAccessor = __webpack_require__(/*! ../internals/function-uncurry-this-accessor */ \"./node_modules/core-js/internals/function-uncurry-this-accessor.js\");\nvar isObject = __webpack_require__(/*! ../internals/is-object */ \"./node_modules/core-js/internals/is-object.js\");\nvar requireObjectCoercible = __webpack_require__(/*! ../internals/require-object-coercible */ \"./node_modules/core-js/internals/require-object-coercible.js\");\nvar aPossiblePrototype = __webpack_require__(/*! ../internals/a-possible-prototype */ \"./node_modules/core-js/internals/a-possible-prototype.js\");\n\n// `Object.setPrototypeOf` method\n// https://tc39.es/ecma262/#sec-object.setprototypeof\n// Works with __proto__ only. Old v8 can't work with null proto objects.\n// eslint-disable-next-line es/no-object-setprototypeof -- safe\nmodule.exports = Object.setPrototypeOf || ('__proto__' in {} ? function () {\n  var CORRECT_SETTER = false;\n  var test = {};\n  var setter;\n  try {\n    setter = uncurryThisAccessor(Object.prototype, '__proto__', 'set');\n    setter(test, []);\n    CORRECT_SETTER = test instanceof Array;\n  } catch (error) { /* empty */ }\n  return function setPrototypeOf(O, proto) {\n    requireObjectCoercible(O);\n    aPossiblePrototype(proto);\n    if (!isObject(O)) return O;\n    if (CORRECT_SETTER) setter(O, proto);\n    else O.__proto__ = proto;\n    return O;\n  };\n}() : undefined);\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/object-set-prototype-of.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/object-to-string.js"
/*!************************************************************!*\
  !*** ./node_modules/core-js/internals/object-to-string.js ***!
  \************************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar TO_STRING_TAG_SUPPORT = __webpack_require__(/*! ../internals/to-string-tag-support */ \"./node_modules/core-js/internals/to-string-tag-support.js\");\nvar classof = __webpack_require__(/*! ../internals/classof */ \"./node_modules/core-js/internals/classof.js\");\n\n// `Object.prototype.toString` method implementation\n// https://tc39.es/ecma262/#sec-object.prototype.tostring\nmodule.exports = TO_STRING_TAG_SUPPORT ? {}.toString : function toString() {\n  return '[object ' + classof(this) + ']';\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/object-to-string.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/ordinary-to-primitive.js"
/*!*****************************************************************!*\
  !*** ./node_modules/core-js/internals/ordinary-to-primitive.js ***!
  \*****************************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar call = __webpack_require__(/*! ../internals/function-call */ \"./node_modules/core-js/internals/function-call.js\");\nvar isCallable = __webpack_require__(/*! ../internals/is-callable */ \"./node_modules/core-js/internals/is-callable.js\");\nvar isObject = __webpack_require__(/*! ../internals/is-object */ \"./node_modules/core-js/internals/is-object.js\");\n\nvar $TypeError = TypeError;\n\n// `OrdinaryToPrimitive` abstract operation\n// https://tc39.es/ecma262/#sec-ordinarytoprimitive\nmodule.exports = function (input, pref) {\n  var fn, val;\n  if (pref === 'string' && isCallable(fn = input.toString) && !isObject(val = call(fn, input))) return val;\n  if (isCallable(fn = input.valueOf) && !isObject(val = call(fn, input))) return val;\n  if (pref !== 'string' && isCallable(fn = input.toString) && !isObject(val = call(fn, input))) return val;\n  throw new $TypeError(\"Can't convert object to primitive value\");\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/ordinary-to-primitive.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/own-keys.js"
/*!****************************************************!*\
  !*** ./node_modules/core-js/internals/own-keys.js ***!
  \****************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar getBuiltIn = __webpack_require__(/*! ../internals/get-built-in */ \"./node_modules/core-js/internals/get-built-in.js\");\nvar uncurryThis = __webpack_require__(/*! ../internals/function-uncurry-this */ \"./node_modules/core-js/internals/function-uncurry-this.js\");\nvar getOwnPropertyNamesModule = __webpack_require__(/*! ../internals/object-get-own-property-names */ \"./node_modules/core-js/internals/object-get-own-property-names.js\");\nvar getOwnPropertySymbolsModule = __webpack_require__(/*! ../internals/object-get-own-property-symbols */ \"./node_modules/core-js/internals/object-get-own-property-symbols.js\");\nvar anObject = __webpack_require__(/*! ../internals/an-object */ \"./node_modules/core-js/internals/an-object.js\");\n\nvar concat = uncurryThis([].concat);\n\n// all object keys, includes non-enumerable and symbols\nmodule.exports = getBuiltIn('Reflect', 'ownKeys') || function ownKeys(it) {\n  var keys = getOwnPropertyNamesModule.f(anObject(it));\n  var getOwnPropertySymbols = getOwnPropertySymbolsModule.f;\n  return getOwnPropertySymbols ? concat(keys, getOwnPropertySymbols(it)) : keys;\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/own-keys.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/path.js"
/*!************************************************!*\
  !*** ./node_modules/core-js/internals/path.js ***!
  \************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar globalThis = __webpack_require__(/*! ../internals/global-this */ \"./node_modules/core-js/internals/global-this.js\");\n\nmodule.exports = globalThis;\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/path.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/regexp-flags-detection.js"
/*!******************************************************************!*\
  !*** ./node_modules/core-js/internals/regexp-flags-detection.js ***!
  \******************************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar globalThis = __webpack_require__(/*! ../internals/global-this */ \"./node_modules/core-js/internals/global-this.js\");\nvar fails = __webpack_require__(/*! ../internals/fails */ \"./node_modules/core-js/internals/fails.js\");\n\n// babel-minify and Closure Compiler transpiles RegExp('.', 'd') -> /./d and it causes SyntaxError\nvar RegExp = globalThis.RegExp;\n\nvar FLAGS_GETTER_IS_CORRECT = !fails(function () {\n  var INDICES_SUPPORT = true;\n  try {\n    RegExp('.', 'd');\n  } catch (error) {\n    INDICES_SUPPORT = false;\n  }\n\n  var O = {};\n  // modern V8 bug\n  var calls = '';\n  var expected = INDICES_SUPPORT ? 'dgimsy' : 'gimsy';\n\n  var addGetter = function (key, chr) {\n    // eslint-disable-next-line es/no-object-defineproperty -- safe\n    Object.defineProperty(O, key, { get: function () {\n      calls += chr;\n      return true;\n    } });\n  };\n\n  var pairs = {\n    dotAll: 's',\n    global: 'g',\n    ignoreCase: 'i',\n    multiline: 'm',\n    sticky: 'y'\n  };\n\n  if (INDICES_SUPPORT) pairs.hasIndices = 'd';\n\n  for (var key in pairs) addGetter(key, pairs[key]);\n\n  // eslint-disable-next-line es/no-object-getownpropertydescriptor -- safe\n  var result = Object.getOwnPropertyDescriptor(RegExp.prototype, 'flags').get.call(O);\n\n  return result !== expected || calls !== expected;\n});\n\nmodule.exports = { correct: FLAGS_GETTER_IS_CORRECT };\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/regexp-flags-detection.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/regexp-flags.js"
/*!********************************************************!*\
  !*** ./node_modules/core-js/internals/regexp-flags.js ***!
  \********************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar anObject = __webpack_require__(/*! ../internals/an-object */ \"./node_modules/core-js/internals/an-object.js\");\n\n// `RegExp.prototype.flags` getter implementation\n// https://tc39.es/ecma262/#sec-get-regexp.prototype.flags\nmodule.exports = function () {\n  var that = anObject(this);\n  var result = '';\n  if (that.hasIndices) result += 'd';\n  if (that.global) result += 'g';\n  if (that.ignoreCase) result += 'i';\n  if (that.multiline) result += 'm';\n  if (that.dotAll) result += 's';\n  if (that.unicode) result += 'u';\n  if (that.unicodeSets) result += 'v';\n  if (that.sticky) result += 'y';\n  return result;\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/regexp-flags.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/regexp-get-flags.js"
/*!************************************************************!*\
  !*** ./node_modules/core-js/internals/regexp-get-flags.js ***!
  \************************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar call = __webpack_require__(/*! ../internals/function-call */ \"./node_modules/core-js/internals/function-call.js\");\nvar hasOwn = __webpack_require__(/*! ../internals/has-own-property */ \"./node_modules/core-js/internals/has-own-property.js\");\nvar isPrototypeOf = __webpack_require__(/*! ../internals/object-is-prototype-of */ \"./node_modules/core-js/internals/object-is-prototype-of.js\");\nvar regExpFlagsDetection = __webpack_require__(/*! ../internals/regexp-flags-detection */ \"./node_modules/core-js/internals/regexp-flags-detection.js\");\nvar regExpFlagsGetterImplementation = __webpack_require__(/*! ../internals/regexp-flags */ \"./node_modules/core-js/internals/regexp-flags.js\");\n\nvar RegExpPrototype = RegExp.prototype;\n\nmodule.exports = regExpFlagsDetection.correct ? function (it) {\n  return it.flags;\n} : function (it) {\n  return (!regExpFlagsDetection.correct && isPrototypeOf(RegExpPrototype, it) && !hasOwn(it, 'flags'))\n    ? call(regExpFlagsGetterImplementation, it)\n    : it.flags;\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/regexp-get-flags.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/require-object-coercible.js"
/*!********************************************************************!*\
  !*** ./node_modules/core-js/internals/require-object-coercible.js ***!
  \********************************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar isNullOrUndefined = __webpack_require__(/*! ../internals/is-null-or-undefined */ \"./node_modules/core-js/internals/is-null-or-undefined.js\");\n\nvar $TypeError = TypeError;\n\n// `RequireObjectCoercible` abstract operation\n// https://tc39.es/ecma262/#sec-requireobjectcoercible\nmodule.exports = function (it) {\n  if (isNullOrUndefined(it)) throw new $TypeError(\"Can't call method on \" + it);\n  return it;\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/require-object-coercible.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/set-helpers.js"
/*!*******************************************************!*\
  !*** ./node_modules/core-js/internals/set-helpers.js ***!
  \*******************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar uncurryThis = __webpack_require__(/*! ../internals/function-uncurry-this */ \"./node_modules/core-js/internals/function-uncurry-this.js\");\n\n// eslint-disable-next-line es/no-set -- safe\nvar SetPrototype = Set.prototype;\n\nmodule.exports = {\n  // eslint-disable-next-line es/no-set -- safe\n  Set: Set,\n  add: uncurryThis(SetPrototype.add),\n  has: uncurryThis(SetPrototype.has),\n  remove: uncurryThis(SetPrototype['delete']),\n  proto: SetPrototype\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/set-helpers.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/set-iterate.js"
/*!*******************************************************!*\
  !*** ./node_modules/core-js/internals/set-iterate.js ***!
  \*******************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar uncurryThis = __webpack_require__(/*! ../internals/function-uncurry-this */ \"./node_modules/core-js/internals/function-uncurry-this.js\");\nvar iterateSimple = __webpack_require__(/*! ../internals/iterate-simple */ \"./node_modules/core-js/internals/iterate-simple.js\");\nvar SetHelpers = __webpack_require__(/*! ../internals/set-helpers */ \"./node_modules/core-js/internals/set-helpers.js\");\n\nvar Set = SetHelpers.Set;\nvar SetPrototype = SetHelpers.proto;\nvar forEach = uncurryThis(SetPrototype.forEach);\nvar keys = uncurryThis(SetPrototype.keys);\nvar next = keys(new Set()).next;\n\nmodule.exports = function (set, fn, interruptible) {\n  return interruptible ? iterateSimple({ iterator: keys(set), next: next }, fn) : forEach(set, fn);\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/set-iterate.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/set-species.js"
/*!*******************************************************!*\
  !*** ./node_modules/core-js/internals/set-species.js ***!
  \*******************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar getBuiltIn = __webpack_require__(/*! ../internals/get-built-in */ \"./node_modules/core-js/internals/get-built-in.js\");\nvar defineBuiltInAccessor = __webpack_require__(/*! ../internals/define-built-in-accessor */ \"./node_modules/core-js/internals/define-built-in-accessor.js\");\nvar wellKnownSymbol = __webpack_require__(/*! ../internals/well-known-symbol */ \"./node_modules/core-js/internals/well-known-symbol.js\");\nvar DESCRipTORS = __webpack_require__(/*! ../internals/descriptors */ \"./node_modules/core-js/internals/descriptors.js\");\n\nvar SPECIES = wellKnownSymbol('species');\n\nmodule.exports = function (CONSTRUCTOR_NAME) {\n  var Constructor = getBuiltIn(CONSTRUCTOR_NAME);\n\n  if (DESCRipTORS && Constructor && !Constructor[SPECIES]) {\n    defineBuiltInAccessor(Constructor, SPECIES, {\n      configurable: true,\n      get: function () { return this; }\n    });\n  }\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/set-species.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/set-to-string-tag.js"
/*!*************************************************************!*\
  !*** ./node_modules/core-js/internals/set-to-string-tag.js ***!
  \*************************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar defineProperty = (__webpack_require__(/*! ../internals/object-define-property */ \"./node_modules/core-js/internals/object-define-property.js\").f);\nvar hasOwn = __webpack_require__(/*! ../internals/has-own-property */ \"./node_modules/core-js/internals/has-own-property.js\");\nvar wellKnownSymbol = __webpack_require__(/*! ../internals/well-known-symbol */ \"./node_modules/core-js/internals/well-known-symbol.js\");\n\nvar TO_STRING_TAG = wellKnownSymbol('toStringTag');\n\nmodule.exports = function (target, TAG, STATIC) {\n  if (target && !STATIC) target = target.prototype;\n  if (target && !hasOwn(target, TO_STRING_TAG)) {\n    defineProperty(target, TO_STRING_TAG, { configurable: true, value: TAG });\n  }\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/set-to-string-tag.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/shared-key.js"
/*!******************************************************!*\
  !*** ./node_modules/core-js/internals/shared-key.js ***!
  \******************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar shared = __webpack_require__(/*! ../internals/shared */ \"./node_modules/core-js/internals/shared.js\");\nvar uid = __webpack_require__(/*! ../internals/uid */ \"./node_modules/core-js/internals/uid.js\");\n\nvar keys = shared('keys');\n\nmodule.exports = function (key) {\n  return keys[key] || (keys[key] = uid(key));\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/shared-key.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/shared-store.js"
/*!********************************************************!*\
  !*** ./node_modules/core-js/internals/shared-store.js ***!
  \********************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar IS_PURE = __webpack_require__(/*! ../internals/is-pure */ \"./node_modules/core-js/internals/is-pure.js\");\nvar globalThis = __webpack_require__(/*! ../internals/global-this */ \"./node_modules/core-js/internals/global-this.js\");\nvar defineGlobalProperty = __webpack_require__(/*! ../internals/define-global-property */ \"./node_modules/core-js/internals/define-global-property.js\");\n\nvar SHARED = '__core-js_shared__';\nvar store = module.exports = globalThis[SHARED] || defineGlobalProperty(SHARED, {});\n\n(store.versions || (store.versions = [])).push({\n  version: '3.49.0',\n  mode: IS_PURE ? 'pure' : 'global',\n  copyright: '© 2013–2025 Denis Pushkarev (zloirock.ru), 2025–2026 CoreJS Company (core-js.io). All rights reserved.',\n  license: 'https://github.com/zloirock/core-js/blob/v3.49.0/LICENSE',\n  source: 'https://github.com/zloirock/core-js'\n});\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/shared-store.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/shared.js"
/*!**************************************************!*\
  !*** ./node_modules/core-js/internals/shared.js ***!
  \**************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar store = __webpack_require__(/*! ../internals/shared-store */ \"./node_modules/core-js/internals/shared-store.js\");\n\nmodule.exports = function (key, value) {\n  return store[key] || (store[key] = value || {});\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/shared.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/structured-clone-proper-transfer.js"
/*!****************************************************************************!*\
  !*** ./node_modules/core-js/internals/structured-clone-proper-transfer.js ***!
  \****************************************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar globalThis = __webpack_require__(/*! ../internals/global-this */ \"./node_modules/core-js/internals/global-this.js\");\nvar fails = __webpack_require__(/*! ../internals/fails */ \"./node_modules/core-js/internals/fails.js\");\nvar V8 = __webpack_require__(/*! ../internals/environment-v8-version */ \"./node_modules/core-js/internals/environment-v8-version.js\");\nvar ENVIRONMENT = __webpack_require__(/*! ../internals/environment */ \"./node_modules/core-js/internals/environment.js\");\n\nvar structuredClone = globalThis.structuredClone;\n\nmodule.exports = !!structuredClone && !fails(function () {\n  // prevent V8 ArrayBufferDetaching protector cell invalidation and performance degradation\n  // https://github.com/zloirock/core-js/issues/679\n  if ((ENVIRONMENT === 'DENO' && V8 > 92) || (ENVIRONMENT === 'NODE' && V8 > 94) || (ENVIRONMENT === 'BROWSER' && V8 > 97)) return false;\n  var buffer = new ArrayBuffer(8);\n  var clone = structuredClone(buffer, { transfer: [buffer] });\n  return buffer.byteLength !== 0 || clone.byteLength !== 8;\n});\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/structured-clone-proper-transfer.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/symbol-constructor-detection.js"
/*!************************************************************************!*\
  !*** ./node_modules/core-js/internals/symbol-constructor-detection.js ***!
  \************************************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\n/* eslint-disable es/no-symbol -- required for testing */\nvar V8_VERSION = __webpack_require__(/*! ../internals/environment-v8-version */ \"./node_modules/core-js/internals/environment-v8-version.js\");\nvar fails = __webpack_require__(/*! ../internals/fails */ \"./node_modules/core-js/internals/fails.js\");\nvar globalThis = __webpack_require__(/*! ../internals/global-this */ \"./node_modules/core-js/internals/global-this.js\");\n\nvar $String = globalThis.String;\n\n// eslint-disable-next-line es/no-object-getownpropertysymbols -- required for testing\nmodule.exports = !!Object.getOwnPropertySymbols && !fails(function () {\n  var symbol = Symbol('symbol detection');\n  // Chrome 38 Symbol has incorrect toString conversion\n  // `get-own-property-symbols` polyfill symbols converted to object are not Symbol instances\n  // nb: Do not call `String` directly to avoid this being optimized out to `symbol+''` which will,\n  // of course, fail.\n  return !$String(symbol) || !(Object(symbol) instanceof Symbol) ||\n    // Chrome 38-40 symbols are not inherited from DOM collections prototypes to instances\n    !Symbol.sham && V8_VERSION && V8_VERSION < 41;\n});\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/symbol-constructor-detection.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/to-absolute-index.js"
/*!*************************************************************!*\
  !*** ./node_modules/core-js/internals/to-absolute-index.js ***!
  \*************************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar toIntegerOrInfinity = __webpack_require__(/*! ../internals/to-integer-or-infinity */ \"./node_modules/core-js/internals/to-integer-or-infinity.js\");\n\nvar max = Math.max;\nvar min = Math.min;\n\n// Helper for a popular repeating case of the spec:\n// Let integer be ? ToInteger(index).\n// If integer < 0, let result be max((length + integer), 0); else let result be min(integer, length).\nmodule.exports = function (index, length) {\n  var integer = toIntegerOrInfinity(index);\n  return integer < 0 ? max(integer + length, 0) : min(integer, length);\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/to-absolute-index.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/to-indexed-object.js"
/*!*************************************************************!*\
  !*** ./node_modules/core-js/internals/to-indexed-object.js ***!
  \*************************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\n// toObject with fallback for non-array-like ES3 strings\nvar IndexedObject = __webpack_require__(/*! ../internals/indexed-object */ \"./node_modules/core-js/internals/indexed-object.js\");\nvar requireObjectCoercible = __webpack_require__(/*! ../internals/require-object-coercible */ \"./node_modules/core-js/internals/require-object-coercible.js\");\n\nmodule.exports = function (it) {\n  return IndexedObject(requireObjectCoercible(it));\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/to-indexed-object.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/to-integer-or-infinity.js"
/*!******************************************************************!*\
  !*** ./node_modules/core-js/internals/to-integer-or-infinity.js ***!
  \******************************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar trunc = __webpack_require__(/*! ../internals/math-trunc */ \"./node_modules/core-js/internals/math-trunc.js\");\n\n// `ToIntegerOrInfinity` abstract operation\n// https://tc39.es/ecma262/#sec-tointegerorinfinity\nmodule.exports = function (argument) {\n  var number = +argument;\n  // eslint-disable-next-line no-self-compare -- NaN check\n  return number !== number || number === 0 ? 0 : trunc(number);\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/to-integer-or-infinity.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/to-length.js"
/*!*****************************************************!*\
  !*** ./node_modules/core-js/internals/to-length.js ***!
  \*****************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar toIntegerOrInfinity = __webpack_require__(/*! ../internals/to-integer-or-infinity */ \"./node_modules/core-js/internals/to-integer-or-infinity.js\");\n\nvar min = Math.min;\n\n// `ToLength` abstract operation\n// https://tc39.es/ecma262/#sec-tolength\nmodule.exports = function (argument) {\n  var len = toIntegerOrInfinity(argument);\n  return len > 0 ? min(len, 0x1FFFFFFFFFFFFF) : 0; // 2 ** 53 - 1 == 9007199254740991\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/to-length.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/to-object.js"
/*!*****************************************************!*\
  !*** ./node_modules/core-js/internals/to-object.js ***!
  \*****************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar requireObjectCoercible = __webpack_require__(/*! ../internals/require-object-coercible */ \"./node_modules/core-js/internals/require-object-coercible.js\");\n\nvar $Object = Object;\n\n// `ToObject` abstract operation\n// https://tc39.es/ecma262/#sec-toobject\nmodule.exports = function (argument) {\n  return $Object(requireObjectCoercible(argument));\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/to-object.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/to-primitive.js"
/*!********************************************************!*\
  !*** ./node_modules/core-js/internals/to-primitive.js ***!
  \********************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar call = __webpack_require__(/*! ../internals/function-call */ \"./node_modules/core-js/internals/function-call.js\");\nvar isObject = __webpack_require__(/*! ../internals/is-object */ \"./node_modules/core-js/internals/is-object.js\");\nvar isSymbol = __webpack_require__(/*! ../internals/is-symbol */ \"./node_modules/core-js/internals/is-symbol.js\");\nvar getMethod = __webpack_require__(/*! ../internals/get-method */ \"./node_modules/core-js/internals/get-method.js\");\nvar ordinaryToPrimitive = __webpack_require__(/*! ../internals/ordinary-to-primitive */ \"./node_modules/core-js/internals/ordinary-to-primitive.js\");\nvar wellKnownSymbol = __webpack_require__(/*! ../internals/well-known-symbol */ \"./node_modules/core-js/internals/well-known-symbol.js\");\n\nvar $TypeError = TypeError;\nvar TO_PRIMITIVE = wellKnownSymbol('toPrimitive');\n\n// `ToPrimitive` abstract operation\n// https://tc39.es/ecma262/#sec-toprimitive\nmodule.exports = function (input, pref) {\n  if (!isObject(input) || isSymbol(input)) return input;\n  var exoticToPrim = getMethod(input, TO_PRIMITIVE);\n  var result;\n  if (exoticToPrim) {\n    if (pref === undefined) pref = 'default';\n    result = call(exoticToPrim, input, pref);\n    if (!isObject(result) || isSymbol(result)) return result;\n    throw new $TypeError(\"Can't convert object to primitive value\");\n  }\n  if (pref === undefined) pref = 'number';\n  return ordinaryToPrimitive(input, pref);\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/to-primitive.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/to-property-key.js"
/*!***********************************************************!*\
  !*** ./node_modules/core-js/internals/to-property-key.js ***!
  \***********************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar toPrimitive = __webpack_require__(/*! ../internals/to-primitive */ \"./node_modules/core-js/internals/to-primitive.js\");\nvar isSymbol = __webpack_require__(/*! ../internals/is-symbol */ \"./node_modules/core-js/internals/is-symbol.js\");\n\n// `ToPropertyKey` abstract operation\n// https://tc39.es/ecma262/#sec-topropertykey\nmodule.exports = function (argument) {\n  var key = toPrimitive(argument, 'string');\n  return isSymbol(key) ? key : key + '';\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/to-property-key.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/to-string-tag-support.js"
/*!*****************************************************************!*\
  !*** ./node_modules/core-js/internals/to-string-tag-support.js ***!
  \*****************************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar wellKnownSymbol = __webpack_require__(/*! ../internals/well-known-symbol */ \"./node_modules/core-js/internals/well-known-symbol.js\");\n\nvar TO_STRING_TAG = wellKnownSymbol('toStringTag');\nvar test = {};\n// eslint-disable-next-line unicorn/no-immediate-mutation -- ES3 syntax limitation\ntest[TO_STRING_TAG] = 'z';\n\nmodule.exports = String(test) === '[object z]';\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/to-string-tag-support.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/to-string.js"
/*!*****************************************************!*\
  !*** ./node_modules/core-js/internals/to-string.js ***!
  \*****************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar classof = __webpack_require__(/*! ../internals/classof */ \"./node_modules/core-js/internals/classof.js\");\n\nvar $String = String;\n\nmodule.exports = function (argument) {\n  if (classof(argument) === 'Symbol') throw new TypeError('Cannot convert a Symbol value to a string');\n  return $String(argument);\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/to-string.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/try-to-string.js"
/*!*********************************************************!*\
  !*** ./node_modules/core-js/internals/try-to-string.js ***!
  \*********************************************************/
(module) {

eval("{\nvar $String = String;\n\nmodule.exports = function (argument) {\n  try {\n    return $String(argument);\n  } catch (error) {\n    return 'Object';\n  }\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/try-to-string.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/uid.js"
/*!***********************************************!*\
  !*** ./node_modules/core-js/internals/uid.js ***!
  \***********************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar uncurryThis = __webpack_require__(/*! ../internals/function-uncurry-this */ \"./node_modules/core-js/internals/function-uncurry-this.js\");\n\nvar id = 0;\nvar postfix = Math.random();\nvar toString = uncurryThis(1.1.toString);\n\nmodule.exports = function (key) {\n  return 'Symbol(' + (key === undefined ? '' : key) + ')_' + toString(++id + postfix, 36);\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/uid.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/use-symbol-as-uid.js"
/*!*************************************************************!*\
  !*** ./node_modules/core-js/internals/use-symbol-as-uid.js ***!
  \*************************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\n/* eslint-disable es/no-symbol -- required for testing */\nvar NATIVE_SYMBOL = __webpack_require__(/*! ../internals/symbol-constructor-detection */ \"./node_modules/core-js/internals/symbol-constructor-detection.js\");\n\nmodule.exports = NATIVE_SYMBOL &&\n  !Symbol.sham &&\n  typeof Symbol.iterator == 'symbol';\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/use-symbol-as-uid.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/v8-prototype-define-bug.js"
/*!*******************************************************************!*\
  !*** ./node_modules/core-js/internals/v8-prototype-define-bug.js ***!
  \*******************************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar DESCRipTORS = __webpack_require__(/*! ../internals/descriptors */ \"./node_modules/core-js/internals/descriptors.js\");\nvar fails = __webpack_require__(/*! ../internals/fails */ \"./node_modules/core-js/internals/fails.js\");\n\n// V8 ~ Chrome 36-\n// https://bugs.chromium.org/p/v8/issues/detail?id=3334\nmodule.exports = DESCRipTORS && fails(function () {\n  // eslint-disable-next-line es/no-object-defineproperty -- required for testing\n  return Object.defineProperty(function () { /* empty */ }, 'prototype', {\n    value: 42,\n    writable: false\n  }).prototype !== 42;\n});\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/v8-prototype-define-bug.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/validate-arguments-length.js"
/*!*********************************************************************!*\
  !*** ./node_modules/core-js/internals/validate-arguments-length.js ***!
  \*********************************************************************/
(module) {

eval("{\nvar $TypeError = TypeError;\n\nmodule.exports = function (passed, required) {\n  if (passed < required) throw new $TypeError('Not enough arguments');\n  return passed;\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/validate-arguments-length.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/weak-map-basic-detection.js"
/*!********************************************************************!*\
  !*** ./node_modules/core-js/internals/weak-map-basic-detection.js ***!
  \********************************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar globalThis = __webpack_require__(/*! ../internals/global-this */ \"./node_modules/core-js/internals/global-this.js\");\nvar isCallable = __webpack_require__(/*! ../internals/is-callable */ \"./node_modules/core-js/internals/is-callable.js\");\n\nvar WeakMap = globalThis.WeakMap;\n\nmodule.exports = isCallable(WeakMap) && /native code/.test(String(WeakMap));\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/weak-map-basic-detection.js?\n}");

/***/ },

/***/ "./node_modules/core-js/internals/well-known-symbol.js"
/*!*************************************************************!*\
  !*** ./node_modules/core-js/internals/well-known-symbol.js ***!
  \*************************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar globalThis = __webpack_require__(/*! ../internals/global-this */ \"./node_modules/core-js/internals/global-this.js\");\nvar shared = __webpack_require__(/*! ../internals/shared */ \"./node_modules/core-js/internals/shared.js\");\nvar hasOwn = __webpack_require__(/*! ../internals/has-own-property */ \"./node_modules/core-js/internals/has-own-property.js\");\nvar uid = __webpack_require__(/*! ../internals/uid */ \"./node_modules/core-js/internals/uid.js\");\nvar NATIVE_SYMBOL = __webpack_require__(/*! ../internals/symbol-constructor-detection */ \"./node_modules/core-js/internals/symbol-constructor-detection.js\");\nvar USE_SYMBOL_AS_UID = __webpack_require__(/*! ../internals/use-symbol-as-uid */ \"./node_modules/core-js/internals/use-symbol-as-uid.js\");\n\nvar Symbol = globalThis.Symbol;\nvar WellKnownSymbolsStore = shared('wks');\nvar createWellKnownSymbol = USE_SYMBOL_AS_UID ? Symbol['for'] || Symbol : Symbol && Symbol.withoutSetter || uid;\n\nmodule.exports = function (name) {\n  if (!hasOwn(WellKnownSymbolsStore, name)) {\n    WellKnownSymbolsStore[name] = NATIVE_SYMBOL && hasOwn(Symbol, name)\n      ? Symbol[name]\n      : createWellKnownSymbol('Symbol.' + name);\n  } return WellKnownSymbolsStore[name];\n};\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/internals/well-known-symbol.js?\n}");

/***/ },

/***/ "./node_modules/core-js/modules/es.array.iterator.js"
/*!***********************************************************!*\
  !*** ./node_modules/core-js/modules/es.array.iterator.js ***!
  \***********************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar toIndexedObject = __webpack_require__(/*! ../internals/to-indexed-object */ \"./node_modules/core-js/internals/to-indexed-object.js\");\nvar addToUnscopables = __webpack_require__(/*! ../internals/add-to-unscopables */ \"./node_modules/core-js/internals/add-to-unscopables.js\");\nvar Iterators = __webpack_require__(/*! ../internals/iterators */ \"./node_modules/core-js/internals/iterators.js\");\nvar InternalStateModule = __webpack_require__(/*! ../internals/internal-state */ \"./node_modules/core-js/internals/internal-state.js\");\nvar defineProperty = (__webpack_require__(/*! ../internals/object-define-property */ \"./node_modules/core-js/internals/object-define-property.js\").f);\nvar defineIterator = __webpack_require__(/*! ../internals/iterator-define */ \"./node_modules/core-js/internals/iterator-define.js\");\nvar createIterResultObject = __webpack_require__(/*! ../internals/create-iter-result-object */ \"./node_modules/core-js/internals/create-iter-result-object.js\");\nvar IS_PURE = __webpack_require__(/*! ../internals/is-pure */ \"./node_modules/core-js/internals/is-pure.js\");\nvar DESCRipTORS = __webpack_require__(/*! ../internals/descriptors */ \"./node_modules/core-js/internals/descriptors.js\");\n\nvar ARRAY_ITERATOR = 'Array Iterator';\nvar setInternalState = InternalStateModule.set;\nvar getInternalState = InternalStateModule.getterFor(ARRAY_ITERATOR);\n\n// `Array.prototype.entries` method\n// https://tc39.es/ecma262/#sec-array.prototype.entries\n// `Array.prototype.keys` method\n// https://tc39.es/ecma262/#sec-array.prototype.keys\n// `Array.prototype.values` method\n// https://tc39.es/ecma262/#sec-array.prototype.values\n// `Array.prototype[@@iterator]` method\n// https://tc39.es/ecma262/#sec-array.prototype-@@iterator\n// `CreateArrayIterator` internal method\n// https://tc39.es/ecma262/#sec-createarrayiterator\nmodule.exports = defineIterator(Array, 'Array', function (iterated, kind) {\n  setInternalState(this, {\n    type: ARRAY_ITERATOR,\n    target: toIndexedObject(iterated), // target\n    index: 0,                          // next index\n    kind: kind                         // kind\n  });\n// `%ArrayIteratorPrototype%.next` method\n// https://tc39.es/ecma262/#sec-%arrayiteratorprototype%.next\n}, function () {\n  var state = getInternalState(this);\n  var target = state.target;\n  var index = state.index++;\n  if (!target || index >= target.length) {\n    state.target = null;\n    return createIterResultObject(undefined, true);\n  }\n  switch (state.kind) {\n    case 'keys': return createIterResultObject(index, false);\n    case 'values': return createIterResultObject(target[index], false);\n  } return createIterResultObject([index, target[index]], false);\n}, 'values');\n\n// argumentsList[@@iterator] is %ArrayProto_values%\n// https://tc39.es/ecma262/#sec-createunmappedargumentsobject\n// https://tc39.es/ecma262/#sec-createmappedargumentsobject\nvar values = Iterators.Arguments = Iterators.Array;\n\n// https://tc39.es/ecma262/#sec-array.prototype-@@unscopables\naddToUnscopables('keys');\naddToUnscopables('values');\naddToUnscopables('entries');\n\n// V8 ~ Chrome 45- bug\nif (!IS_PURE && DESCRipTORS && values.name !== 'values') try {\n  defineProperty(values, 'name', { value: 'values' });\n} catch (error) { /* empty */ }\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/modules/es.array.iterator.js?\n}");

/***/ },

/***/ "./node_modules/core-js/modules/es.error.to-string.js"
/*!************************************************************!*\
  !*** ./node_modules/core-js/modules/es.error.to-string.js ***!
  \************************************************************/
(__unused_webpack_module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar defineBuiltIn = __webpack_require__(/*! ../internals/define-built-in */ \"./node_modules/core-js/internals/define-built-in.js\");\nvar errorToString = __webpack_require__(/*! ../internals/error-to-string */ \"./node_modules/core-js/internals/error-to-string.js\");\n\nvar ErrorPrototype = Error.prototype;\n\n// `Error.prototype.toString` method fix\n// https://tc39.es/ecma262/#sec-error.prototype.tostring\nif (ErrorPrototype.toString !== errorToString) {\n  defineBuiltIn(ErrorPrototype, 'toString', errorToString);\n}\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/modules/es.error.to-string.js?\n}");

/***/ },

/***/ "./node_modules/core-js/modules/es.map.constructor.js"
/*!************************************************************!*\
  !*** ./node_modules/core-js/modules/es.map.constructor.js ***!
  \************************************************************/
(__unused_webpack_module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar collection = __webpack_require__(/*! ../internals/collection */ \"./node_modules/core-js/internals/collection.js\");\nvar collectionStrong = __webpack_require__(/*! ../internals/collection-strong */ \"./node_modules/core-js/internals/collection-strong.js\");\n\n// `Map` constructor\n// https://tc39.es/ecma262/#sec-map-objects\ncollection('Map', function (init) {\n  return function Map() { return init(this, arguments.length ? arguments[0] : undefined); };\n}, collectionStrong);\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/modules/es.map.constructor.js?\n}");

/***/ },

/***/ "./node_modules/core-js/modules/es.map.js"
/*!************************************************!*\
  !*** ./node_modules/core-js/modules/es.map.js ***!
  \************************************************/
(__unused_webpack_module, __unused_webpack_exports, __webpack_require__) {

eval("{\n// TODO: Remove this module from `core-js@4` since it's replaced to module below\n__webpack_require__(/*! ../modules/es.map.constructor */ \"./node_modules/core-js/modules/es.map.constructor.js\");\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/modules/es.map.js?\n}");

/***/ },

/***/ "./node_modules/core-js/modules/es.object.keys.js"
/*!********************************************************!*\
  !*** ./node_modules/core-js/modules/es.object.keys.js ***!
  \********************************************************/
(__unused_webpack_module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar $ = __webpack_require__(/*! ../internals/export */ \"./node_modules/core-js/internals/export.js\");\nvar toObject = __webpack_require__(/*! ../internals/to-object */ \"./node_modules/core-js/internals/to-object.js\");\nvar nativeKeys = __webpack_require__(/*! ../internals/object-keys */ \"./node_modules/core-js/internals/object-keys.js\");\nvar fails = __webpack_require__(/*! ../internals/fails */ \"./node_modules/core-js/internals/fails.js\");\n\nvar FAILS_ON_PRIMITIVES = fails(function () { nativeKeys(1); });\n\n// `Object.keys` method\n// https://tc39.es/ecma262/#sec-object.keys\n$({ target: 'Object', stat: true, forced: FAILS_ON_PRIMITIVES }, {\n  keys: function keys(it) {\n    return nativeKeys(toObject(it));\n  }\n});\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/modules/es.object.keys.js?\n}");

/***/ },

/***/ "./node_modules/core-js/modules/es.object.to-string.js"
/*!*************************************************************!*\
  !*** ./node_modules/core-js/modules/es.object.to-string.js ***!
  \*************************************************************/
(__unused_webpack_module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar TO_STRING_TAG_SUPPORT = __webpack_require__(/*! ../internals/to-string-tag-support */ \"./node_modules/core-js/internals/to-string-tag-support.js\");\nvar defineBuiltIn = __webpack_require__(/*! ../internals/define-built-in */ \"./node_modules/core-js/internals/define-built-in.js\");\nvar toString = __webpack_require__(/*! ../internals/object-to-string */ \"./node_modules/core-js/internals/object-to-string.js\");\n\n// `Object.prototype.toString` method\n// https://tc39.es/ecma262/#sec-object.prototype.tostring\nif (!TO_STRING_TAG_SUPPORT) {\n  defineBuiltIn(Object.prototype, 'toString', toString, { unsafe: true });\n}\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/modules/es.object.to-string.js?\n}");

/***/ },

/***/ "./node_modules/core-js/modules/es.set.constructor.js"
/*!************************************************************!*\
  !*** ./node_modules/core-js/modules/es.set.constructor.js ***!
  \************************************************************/
(__unused_webpack_module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar collection = __webpack_require__(/*! ../internals/collection */ \"./node_modules/core-js/internals/collection.js\");\nvar collectionStrong = __webpack_require__(/*! ../internals/collection-strong */ \"./node_modules/core-js/internals/collection-strong.js\");\n\n// `Set` constructor\n// https://tc39.es/ecma262/#sec-set-objects\ncollection('Set', function (init) {\n  return function Set() { return init(this, arguments.length ? arguments[0] : undefined); };\n}, collectionStrong);\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/modules/es.set.constructor.js?\n}");

/***/ },

/***/ "./node_modules/core-js/modules/es.set.js"
/*!************************************************!*\
  !*** ./node_modules/core-js/modules/es.set.js ***!
  \************************************************/
(__unused_webpack_module, __unused_webpack_exports, __webpack_require__) {

eval("{\n// TODO: Remove this module from `core-js@4` since it's replaced to module below\n__webpack_require__(/*! ../modules/es.set.constructor */ \"./node_modules/core-js/modules/es.set.constructor.js\");\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/modules/es.set.js?\n}");

/***/ },

/***/ "./node_modules/core-js/modules/esnext.set.add-all.js"
/*!************************************************************!*\
  !*** ./node_modules/core-js/modules/esnext.set.add-all.js ***!
  \************************************************************/
(__unused_webpack_module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar $ = __webpack_require__(/*! ../internals/export */ \"./node_modules/core-js/internals/export.js\");\nvar aSet = __webpack_require__(/*! ../internals/a-set */ \"./node_modules/core-js/internals/a-set.js\");\nvar add = (__webpack_require__(/*! ../internals/set-helpers */ \"./node_modules/core-js/internals/set-helpers.js\").add);\n\n// `Set.prototype.addAll` method\n// https://github.com/tc39/proposal-collection-methods\n$({ target: 'Set', proto: true, real: true, forced: true }, {\n  addAll: function addAll(/* ...elements */) {\n    var set = aSet(this);\n    for (var k = 0, len = arguments.length; k < len; k++) {\n      add(set, arguments[k]);\n    } return set;\n  }\n});\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/modules/esnext.set.add-all.js?\n}");

/***/ },

/***/ "./node_modules/core-js/modules/esnext.set.delete-all.js"
/*!***************************************************************!*\
  !*** ./node_modules/core-js/modules/esnext.set.delete-all.js ***!
  \***************************************************************/
(__unused_webpack_module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar $ = __webpack_require__(/*! ../internals/export */ \"./node_modules/core-js/internals/export.js\");\nvar aSet = __webpack_require__(/*! ../internals/a-set */ \"./node_modules/core-js/internals/a-set.js\");\nvar remove = (__webpack_require__(/*! ../internals/set-helpers */ \"./node_modules/core-js/internals/set-helpers.js\").remove);\n\n// `Set.prototype.deleteAll` method\n// https://github.com/tc39/proposal-collection-methods\n$({ target: 'Set', proto: true, real: true, forced: true }, {\n  deleteAll: function deleteAll(/* ...elements */) {\n    var collection = aSet(this);\n    var allDeleted = true;\n    var wasDeleted;\n    for (var k = 0, len = arguments.length; k < len; k++) {\n      wasDeleted = remove(collection, arguments[k]);\n      allDeleted = allDeleted && wasDeleted;\n    } return !!allDeleted;\n  }\n});\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/modules/esnext.set.delete-all.js?\n}");

/***/ },

/***/ "./node_modules/core-js/modules/web.dom-exception.constructor.js"
/*!***********************************************************************!*\
  !*** ./node_modules/core-js/modules/web.dom-exception.constructor.js ***!
  \***********************************************************************/
(__unused_webpack_module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar $ = __webpack_require__(/*! ../internals/export */ \"./node_modules/core-js/internals/export.js\");\nvar getBuiltIn = __webpack_require__(/*! ../internals/get-built-in */ \"./node_modules/core-js/internals/get-built-in.js\");\nvar getBuiltInNodeModule = __webpack_require__(/*! ../internals/get-built-in-node-module */ \"./node_modules/core-js/internals/get-built-in-node-module.js\");\nvar fails = __webpack_require__(/*! ../internals/fails */ \"./node_modules/core-js/internals/fails.js\");\nvar create = __webpack_require__(/*! ../internals/object-create */ \"./node_modules/core-js/internals/object-create.js\");\nvar createPropertyDescriptor = __webpack_require__(/*! ../internals/create-property-descriptor */ \"./node_modules/core-js/internals/create-property-descriptor.js\");\nvar defineProperty = (__webpack_require__(/*! ../internals/object-define-property */ \"./node_modules/core-js/internals/object-define-property.js\").f);\nvar defineBuiltIn = __webpack_require__(/*! ../internals/define-built-in */ \"./node_modules/core-js/internals/define-built-in.js\");\nvar defineBuiltInAccessor = __webpack_require__(/*! ../internals/define-built-in-accessor */ \"./node_modules/core-js/internals/define-built-in-accessor.js\");\nvar hasOwn = __webpack_require__(/*! ../internals/has-own-property */ \"./node_modules/core-js/internals/has-own-property.js\");\nvar anInstance = __webpack_require__(/*! ../internals/an-instance */ \"./node_modules/core-js/internals/an-instance.js\");\nvar anObject = __webpack_require__(/*! ../internals/an-object */ \"./node_modules/core-js/internals/an-object.js\");\nvar errorToString = __webpack_require__(/*! ../internals/error-to-string */ \"./node_modules/core-js/internals/error-to-string.js\");\nvar normalizeStringArgument = __webpack_require__(/*! ../internals/normalize-string-argument */ \"./node_modules/core-js/internals/normalize-string-argument.js\");\nvar DOMExceptionConstants = __webpack_require__(/*! ../internals/dom-exception-constants */ \"./node_modules/core-js/internals/dom-exception-constants.js\");\nvar clearErrorStack = __webpack_require__(/*! ../internals/error-stack-clear */ \"./node_modules/core-js/internals/error-stack-clear.js\");\nvar InternalStateModule = __webpack_require__(/*! ../internals/internal-state */ \"./node_modules/core-js/internals/internal-state.js\");\nvar DESCRipTORS = __webpack_require__(/*! ../internals/descriptors */ \"./node_modules/core-js/internals/descriptors.js\");\nvar IS_PURE = __webpack_require__(/*! ../internals/is-pure */ \"./node_modules/core-js/internals/is-pure.js\");\n\nvar DOM_EXCEPTION = 'DOMException';\nvar DATA_CLONE_ERR = 'DATA_CLONE_ERR';\nvar Error = getBuiltIn('Error');\n// NodeJS < 17.0 does not expose `DOMException` to global\nvar NativeDOMException = getBuiltIn(DOM_EXCEPTION) || (function () {\n  try {\n    // NodeJS < 15.0 does not expose `MessageChannel` to global\n    var MessageChannel = getBuiltIn('MessageChannel') || getBuiltInNodeModule('worker_threads').MessageChannel;\n    // eslint-disable-next-line es/no-weak-map, unicorn/require-post-message-target-origin -- safe\n    new MessageChannel().port1.postMessage(new WeakMap());\n  } catch (error) {\n    if (error.name === DATA_CLONE_ERR && error.code === 25) return error.constructor;\n  }\n})();\nvar NativeDOMExceptionPrototype = NativeDOMException && NativeDOMException.prototype;\nvar ErrorPrototype = Error.prototype;\nvar setInternalState = InternalStateModule.set;\nvar getInternalState = InternalStateModule.getterFor(DOM_EXCEPTION);\nvar HAS_STACK = 'stack' in new Error(DOM_EXCEPTION);\n\nvar codeFor = function (name) {\n  return hasOwn(DOMExceptionConstants, name) && DOMExceptionConstants[name].m ? DOMExceptionConstants[name].c : 0;\n};\n\nvar $DOMException = function DOMException() {\n  anInstance(this, DOMExceptionPrototype);\n  var argumentsLength = arguments.length;\n  var message = normalizeStringArgument(argumentsLength < 1 ? undefined : arguments[0]);\n  var name = normalizeStringArgument(argumentsLength < 2 ? undefined : arguments[1], 'Error');\n  var code = codeFor(name);\n  setInternalState(this, {\n    type: DOM_EXCEPTION,\n    name: name,\n    message: message,\n    code: code\n  });\n  if (!DESCRipTORS) {\n    this.name = name;\n    this.message = message;\n    this.code = code;\n  }\n  if (HAS_STACK) {\n    var error = new Error(message);\n    error.name = DOM_EXCEPTION;\n    defineProperty(this, 'stack', createPropertyDescriptor(1, clearErrorStack(error.stack, 1)));\n  }\n};\n\nvar DOMExceptionPrototype = $DOMException.prototype = create(ErrorPrototype);\n\nvar createGetterDescriptor = function (get) {\n  return { enumerable: true, configurable: true, get: get };\n};\n\nvar getterFor = function (key) {\n  return createGetterDescriptor(function () {\n    return getInternalState(this)[key];\n  });\n};\n\nif (DESCRipTORS) {\n  // `DOMException.prototype.code` getter\n  defineBuiltInAccessor(DOMExceptionPrototype, 'code', getterFor('code'));\n  // `DOMException.prototype.message` getter\n  defineBuiltInAccessor(DOMExceptionPrototype, 'message', getterFor('message'));\n  // `DOMException.prototype.name` getter\n  defineBuiltInAccessor(DOMExceptionPrototype, 'name', getterFor('name'));\n}\n\ndefineProperty(DOMExceptionPrototype, 'constructor', createPropertyDescriptor(1, $DOMException));\n\n// FF36- DOMException is a function, but can't be constructed\nvar INCORRECT_CONSTRUCTOR = fails(function () {\n  return !(new NativeDOMException() instanceof Error);\n});\n\n// Safari 10.1 / Chrome 32- / IE8- DOMException.prototype.toString bugs\nvar INCORRECT_TO_STRING = INCORRECT_CONSTRUCTOR || fails(function () {\n  return ErrorPrototype.toString !== errorToString || String(new NativeDOMException(1, 2)) !== '2: 1';\n});\n\n// Deno 1.6.3- DOMException.prototype.code just missed\nvar INCORRECT_CODE = INCORRECT_CONSTRUCTOR || fails(function () {\n  return new NativeDOMException(1, 'DataCloneError').code !== 25;\n});\n\n// Deno 1.6.3- DOMException constants just missed\nvar MISSED_CONSTANTS = INCORRECT_CONSTRUCTOR\n  || NativeDOMException[DATA_CLONE_ERR] !== 25\n  || NativeDOMExceptionPrototype[DATA_CLONE_ERR] !== 25;\n\nvar FORCED_CONSTRUCTOR = IS_PURE ? INCORRECT_TO_STRING || INCORRECT_CODE || MISSED_CONSTANTS : INCORRECT_CONSTRUCTOR;\n\n// `DOMException` constructor\n// https://webidl.spec.whatwg.org/#idl-DOMException\n$({ global: true, constructor: true, forced: FORCED_CONSTRUCTOR }, {\n  DOMException: FORCED_CONSTRUCTOR ? $DOMException : NativeDOMException\n});\n\nvar PolyfilledDOMException = getBuiltIn(DOM_EXCEPTION);\nvar PolyfilledDOMExceptionPrototype = PolyfilledDOMException.prototype;\n\nif (INCORRECT_TO_STRING && (IS_PURE || NativeDOMException === PolyfilledDOMException)) {\n  defineBuiltIn(PolyfilledDOMExceptionPrototype, 'toString', errorToString);\n}\n\nif (INCORRECT_CODE && DESCRipTORS && NativeDOMException === PolyfilledDOMException) {\n  defineBuiltInAccessor(PolyfilledDOMExceptionPrototype, 'code', createGetterDescriptor(function () {\n    return codeFor(anObject(this).name);\n  }));\n}\n\n// `DOMException` constants\nfor (var key in DOMExceptionConstants) if (hasOwn(DOMExceptionConstants, key)) {\n  var constant = DOMExceptionConstants[key];\n  var constantName = constant.s;\n  var descriptor = createPropertyDescriptor(6, constant.c);\n  if (!hasOwn(PolyfilledDOMException, constantName)) {\n    defineProperty(PolyfilledDOMException, constantName, descriptor);\n  }\n  if (!hasOwn(PolyfilledDOMExceptionPrototype, constantName)) {\n    defineProperty(PolyfilledDOMExceptionPrototype, constantName, descriptor);\n  }\n}\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/modules/web.dom-exception.constructor.js?\n}");

/***/ },

/***/ "./node_modules/core-js/modules/web.dom-exception.stack.js"
/*!*****************************************************************!*\
  !*** ./node_modules/core-js/modules/web.dom-exception.stack.js ***!
  \*****************************************************************/
(__unused_webpack_module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar $ = __webpack_require__(/*! ../internals/export */ \"./node_modules/core-js/internals/export.js\");\nvar globalThis = __webpack_require__(/*! ../internals/global-this */ \"./node_modules/core-js/internals/global-this.js\");\nvar getBuiltIn = __webpack_require__(/*! ../internals/get-built-in */ \"./node_modules/core-js/internals/get-built-in.js\");\nvar createPropertyDescriptor = __webpack_require__(/*! ../internals/create-property-descriptor */ \"./node_modules/core-js/internals/create-property-descriptor.js\");\nvar defineProperty = (__webpack_require__(/*! ../internals/object-define-property */ \"./node_modules/core-js/internals/object-define-property.js\").f);\nvar hasOwn = __webpack_require__(/*! ../internals/has-own-property */ \"./node_modules/core-js/internals/has-own-property.js\");\nvar anInstance = __webpack_require__(/*! ../internals/an-instance */ \"./node_modules/core-js/internals/an-instance.js\");\nvar inheritIfRequired = __webpack_require__(/*! ../internals/inherit-if-required */ \"./node_modules/core-js/internals/inherit-if-required.js\");\nvar normalizeStringArgument = __webpack_require__(/*! ../internals/normalize-string-argument */ \"./node_modules/core-js/internals/normalize-string-argument.js\");\nvar DOMExceptionConstants = __webpack_require__(/*! ../internals/dom-exception-constants */ \"./node_modules/core-js/internals/dom-exception-constants.js\");\nvar clearErrorStack = __webpack_require__(/*! ../internals/error-stack-clear */ \"./node_modules/core-js/internals/error-stack-clear.js\");\nvar DESCRipTORS = __webpack_require__(/*! ../internals/descriptors */ \"./node_modules/core-js/internals/descriptors.js\");\nvar IS_PURE = __webpack_require__(/*! ../internals/is-pure */ \"./node_modules/core-js/internals/is-pure.js\");\n\nvar DOM_EXCEPTION = 'DOMException';\nvar Error = getBuiltIn('Error');\nvar NativeDOMException = getBuiltIn(DOM_EXCEPTION);\n\nvar $DOMException = function DOMException() {\n  anInstance(this, DOMExceptionPrototype);\n  var argumentsLength = arguments.length;\n  var message = normalizeStringArgument(argumentsLength < 1 ? undefined : arguments[0]);\n  var name = normalizeStringArgument(argumentsLength < 2 ? undefined : arguments[1], 'Error');\n  var that = new NativeDOMException(message, name);\n  var error = new Error(message);\n  error.name = DOM_EXCEPTION;\n  defineProperty(that, 'stack', createPropertyDescriptor(1, clearErrorStack(error.stack, 1)));\n  inheritIfRequired(that, this, $DOMException);\n  return that;\n};\n\nvar DOMExceptionPrototype = $DOMException.prototype = NativeDOMException.prototype;\n\nvar ERROR_HAS_STACK = 'stack' in new Error(DOM_EXCEPTION);\nvar DOM_EXCEPTION_HAS_STACK = 'stack' in new NativeDOMException(1, 2);\n\n// eslint-disable-next-line es/no-object-getownpropertydescriptor -- safe\nvar descriptor = NativeDOMException && DESCRipTORS && Object.getOwnPropertyDescriptor(globalThis, DOM_EXCEPTION);\n\n// Bun ~ 0.1.1 DOMException have incorrect descriptor and we can't redefine it\n// https://github.com/Jarred-Sumner/bun/issues/399\nvar BUGGY_DESCRipTOR = !!descriptor && !(descriptor.writable && descriptor.configurable);\n\nvar FORCED_CONSTRUCTOR = ERROR_HAS_STACK && !BUGGY_DESCRipTOR && !DOM_EXCEPTION_HAS_STACK;\n\n// `DOMException` constructor patch for `.stack` where it's required\n// https://webidl.spec.whatwg.org/#es-DOMException-specialness\n$({ global: true, constructor: true, forced: IS_PURE || FORCED_CONSTRUCTOR }, { // TODO: fix export logic\n  DOMException: FORCED_CONSTRUCTOR ? $DOMException : NativeDOMException\n});\n\nvar PolyfilledDOMException = getBuiltIn(DOM_EXCEPTION);\nvar PolyfilledDOMExceptionPrototype = PolyfilledDOMException.prototype;\n\nif (PolyfilledDOMExceptionPrototype.constructor !== PolyfilledDOMException) {\n  if (!IS_PURE) {\n    defineProperty(PolyfilledDOMExceptionPrototype, 'constructor', createPropertyDescriptor(1, PolyfilledDOMException));\n  }\n\n  for (var key in DOMExceptionConstants) if (hasOwn(DOMExceptionConstants, key)) {\n    var constant = DOMExceptionConstants[key];\n    var constantName = constant.s;\n    if (!hasOwn(PolyfilledDOMException, constantName)) {\n      defineProperty(PolyfilledDOMException, constantName, createPropertyDescriptor(6, constant.c));\n    }\n  }\n}\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/modules/web.dom-exception.stack.js?\n}");

/***/ },

/***/ "./node_modules/core-js/modules/web.dom-exception.to-string-tag.js"
/*!*************************************************************************!*\
  !*** ./node_modules/core-js/modules/web.dom-exception.to-string-tag.js ***!
  \*************************************************************************/
(__unused_webpack_module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar getBuiltIn = __webpack_require__(/*! ../internals/get-built-in */ \"./node_modules/core-js/internals/get-built-in.js\");\nvar setToStringTag = __webpack_require__(/*! ../internals/set-to-string-tag */ \"./node_modules/core-js/internals/set-to-string-tag.js\");\n\nvar DOM_EXCEPTION = 'DOMException';\n\n// `DOMException.prototype[@@toStringTag]` property\nsetToStringTag(getBuiltIn(DOM_EXCEPTION), DOM_EXCEPTION);\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/modules/web.dom-exception.to-string-tag.js?\n}");

/***/ },

/***/ "./node_modules/core-js/modules/web.structured-clone.js"
/*!**************************************************************!*\
  !*** ./node_modules/core-js/modules/web.structured-clone.js ***!
  \**************************************************************/
(__unused_webpack_module, __unused_webpack_exports, __webpack_require__) {

eval("{\nvar IS_PURE = __webpack_require__(/*! ../internals/is-pure */ \"./node_modules/core-js/internals/is-pure.js\");\nvar $ = __webpack_require__(/*! ../internals/export */ \"./node_modules/core-js/internals/export.js\");\nvar globalThis = __webpack_require__(/*! ../internals/global-this */ \"./node_modules/core-js/internals/global-this.js\");\nvar getBuiltIn = __webpack_require__(/*! ../internals/get-built-in */ \"./node_modules/core-js/internals/get-built-in.js\");\nvar uncurryThis = __webpack_require__(/*! ../internals/function-uncurry-this */ \"./node_modules/core-js/internals/function-uncurry-this.js\");\nvar fails = __webpack_require__(/*! ../internals/fails */ \"./node_modules/core-js/internals/fails.js\");\nvar uid = __webpack_require__(/*! ../internals/uid */ \"./node_modules/core-js/internals/uid.js\");\nvar isCallable = __webpack_require__(/*! ../internals/is-callable */ \"./node_modules/core-js/internals/is-callable.js\");\nvar isConstructor = __webpack_require__(/*! ../internals/is-constructor */ \"./node_modules/core-js/internals/is-constructor.js\");\nvar isNullOrUndefined = __webpack_require__(/*! ../internals/is-null-or-undefined */ \"./node_modules/core-js/internals/is-null-or-undefined.js\");\nvar isObject = __webpack_require__(/*! ../internals/is-object */ \"./node_modules/core-js/internals/is-object.js\");\nvar isSymbol = __webpack_require__(/*! ../internals/is-symbol */ \"./node_modules/core-js/internals/is-symbol.js\");\nvar iterate = __webpack_require__(/*! ../internals/iterate */ \"./node_modules/core-js/internals/iterate.js\");\nvar anObject = __webpack_require__(/*! ../internals/an-object */ \"./node_modules/core-js/internals/an-object.js\");\nvar classof = __webpack_require__(/*! ../internals/classof */ \"./node_modules/core-js/internals/classof.js\");\nvar hasOwn = __webpack_require__(/*! ../internals/has-own-property */ \"./node_modules/core-js/internals/has-own-property.js\");\nvar createProperty = __webpack_require__(/*! ../internals/create-property */ \"./node_modules/core-js/internals/create-property.js\");\nvar createNonEnumerableProperty = __webpack_require__(/*! ../internals/create-non-enumerable-property */ \"./node_modules/core-js/internals/create-non-enumerable-property.js\");\nvar lengthOfArrayLike = __webpack_require__(/*! ../internals/length-of-array-like */ \"./node_modules/core-js/internals/length-of-array-like.js\");\nvar validateArgumentsLength = __webpack_require__(/*! ../internals/validate-arguments-length */ \"./node_modules/core-js/internals/validate-arguments-length.js\");\nvar getRegExpFlags = __webpack_require__(/*! ../internals/regexp-get-flags */ \"./node_modules/core-js/internals/regexp-get-flags.js\");\nvar MapHelpers = __webpack_require__(/*! ../internals/map-helpers */ \"./node_modules/core-js/internals/map-helpers.js\");\nvar SetHelpers = __webpack_require__(/*! ../internals/set-helpers */ \"./node_modules/core-js/internals/set-helpers.js\");\nvar setIterate = __webpack_require__(/*! ../internals/set-iterate */ \"./node_modules/core-js/internals/set-iterate.js\");\nvar detachTransferable = __webpack_require__(/*! ../internals/detach-transferable */ \"./node_modules/core-js/internals/detach-transferable.js\");\nvar ERROR_STACK_INSTALLABLE = __webpack_require__(/*! ../internals/error-stack-installable */ \"./node_modules/core-js/internals/error-stack-installable.js\");\nvar PROPER_STRUCTURED_CLONE_TRANSFER = __webpack_require__(/*! ../internals/structured-clone-proper-transfer */ \"./node_modules/core-js/internals/structured-clone-proper-transfer.js\");\n\nvar Object = globalThis.Object;\nvar Array = globalThis.Array;\nvar Date = globalThis.Date;\nvar Error = globalThis.Error;\nvar TypeError = globalThis.TypeError;\nvar PerformanceMark = globalThis.PerformanceMark;\nvar DOMException = getBuiltIn('DOMException');\nvar Map = MapHelpers.Map;\nvar mapHas = MapHelpers.has;\nvar mapGet = MapHelpers.get;\nvar mapSet = MapHelpers.set;\nvar Set = SetHelpers.Set;\nvar setAdd = SetHelpers.add;\nvar setHas = SetHelpers.has;\nvar objectKeys = getBuiltIn('Object', 'keys');\nvar push = uncurryThis([].push);\nvar thisBooleanValue = uncurryThis(true.valueOf);\nvar thisNumberValue = uncurryThis(1.1.valueOf);\nvar thisStringValue = uncurryThis(''.valueOf);\nvar thisTimeValue = uncurryThis(Date.prototype.getTime);\nvar PERFORMANCE_MARK = uid('structuredClone');\nvar DATA_CLONE_ERROR = 'DataCloneError';\nvar TRANSFERRING = 'Transferring';\n\nvar checkBasicSemantic = function (structuredCloneImplementation) {\n  return !fails(function () {\n    var set1 = new globalThis.Set([7]);\n    var set2 = structuredCloneImplementation(set1);\n    var number = structuredCloneImplementation(Object(7));\n    return set2 === set1 || !set2.has(7) || !isObject(number) || +number !== 7;\n  }) && structuredCloneImplementation;\n};\n\nvar checkErrorsCloning = function (structuredCloneImplementation, $Error) {\n  return !fails(function () {\n    var error = new $Error();\n    var test = structuredCloneImplementation({ a: error, b: error });\n    return !(test && test.a === test.b && test.a instanceof $Error && test.a.stack === error.stack);\n  });\n};\n\n// https://github.com/whatwg/html/pull/5749\nvar checkNewErrorsCloningSemantic = function (structuredCloneImplementation) {\n  return !fails(function () {\n    var test = structuredCloneImplementation(new globalThis.AggregateError([1], PERFORMANCE_MARK, { cause: 3 }));\n    return test.name !== 'AggregateError' || test.errors[0] !== 1 || test.message !== PERFORMANCE_MARK || test.cause !== 3;\n  });\n};\n\n// FF94+, Safari 15.4+, Chrome 98+, NodeJS 17.0+, Deno 1.13+\n// FF<103 and Safari implementations can't clone errors\n// https://bugzilla.mozilla.org/show_bug.cgi?id=1556604\n// FF103 can clone errors, but `.stack` of clone is an empty string\n// https://bugzilla.mozilla.org/show_bug.cgi?id=1778762\n// FF104+ fixed it on usual errors, but not on DOMExceptions\n// https://bugzilla.mozilla.org/show_bug.cgi?id=1777321\n// Chrome <102 returns `null` if cloned object contains multiple references to one error\n// https://bugs.chromium.org/p/v8/issues/detail?id=12542\n// NodeJS implementation can't clone DOMExceptions\n// https://github.com/nodejs/node/issues/41038\n// only FF103+ supports new (html/5749) error cloning semantic\nvar nativeStructuredClone = globalThis.structuredClone;\n\nvar FORCED_REPLACEMENT = IS_PURE\n  || !checkErrorsCloning(nativeStructuredClone, Error)\n  || !checkErrorsCloning(nativeStructuredClone, DOMException)\n  || !checkNewErrorsCloningSemantic(nativeStructuredClone);\n\n// Chrome 82+, Safari 14.1+, Deno 1.11+\n// Chrome 78-81 implementation swaps `.name` and `.message` of cloned `DOMException`\n// Chrome returns `null` if cloned object contains multiple references to one error\n// Safari 14.1 implementation doesn't clone some `RegExp` flags, so requires a workaround\n// Safari implementation can't clone errors\n// Deno 1.2-1.10 implementations too naive\n// NodeJS 16.0+ does not have `PerformanceMark` constructor\n// NodeJS <17.2 structured cloning implementation from `performance.mark` is too naive\n// and can't clone, for example, `RegExp` or some boxed primitives\n// https://github.com/nodejs/node/issues/40840\n// no one of those implementations supports new (html/5749) error cloning semantic\nvar structuredCloneFromMark = !nativeStructuredClone && checkBasicSemantic(function (value) {\n  return new PerformanceMark(PERFORMANCE_MARK, { detail: value }).detail;\n});\n\nvar nativeRestrictedStructuredClone = checkBasicSemantic(nativeStructuredClone) || structuredCloneFromMark;\n\nvar throwUncloneable = function (type) {\n  throw new DOMException('Uncloneable type: ' + type, DATA_CLONE_ERROR);\n};\n\nvar throwUnpolyfillable = function (type, action) {\n  throw new DOMException((action || 'Cloning') + ' of ' + type + ' cannot be properly polyfilled in this engine', DATA_CLONE_ERROR);\n};\n\nvar tryNativeRestrictedStructuredClone = function (value, type) {\n  if (!nativeRestrictedStructuredClone) throwUnpolyfillable(type);\n  return nativeRestrictedStructuredClone(value);\n};\n\nvar createDataTransfer = function () {\n  var dataTransfer;\n  try {\n    dataTransfer = new globalThis.DataTransfer();\n  } catch (error) {\n    try {\n      dataTransfer = new globalThis.ClipboardEvent('').clipboardData;\n    } catch (error2) { /* empty */ }\n  }\n  return dataTransfer && dataTransfer.items && dataTransfer.files ? dataTransfer : null;\n};\n\nvar cloneBuffer = function (value, map, $type) {\n  if (mapHas(map, value)) return mapGet(map, value);\n\n  var type = $type || classof(value);\n  var clone, length, options, source, target, i;\n\n  if (type === 'SharedArrayBuffer') {\n    if (nativeRestrictedStructuredClone) clone = nativeRestrictedStructuredClone(value);\n    // SharedArrayBuffer should use shared memory, we can't polyfill it, so return the original\n    else clone = value;\n  } else {\n    var DataView = globalThis.DataView;\n\n    // `ArrayBuffer#slice` is not available in IE10\n    // `ArrayBuffer#slice` and `DataView` are not available in old FF\n    if (!DataView && !isCallable(value.slice)) throwUnpolyfillable('ArrayBuffer');\n    // detached buffers throws in `DataView` and `.slice`\n    try {\n      if (isCallable(value.slice) && !value.resizable) {\n        clone = value.slice(0);\n      } else {\n        length = value.byteLength;\n        options = 'maxByteLength' in value ? { maxByteLength: value.maxByteLength } : undefined;\n        // eslint-disable-next-line es/no-resizable-and-growable-arraybuffers -- safe\n        clone = new ArrayBuffer(length, options);\n        source = new DataView(value);\n        target = new DataView(clone);\n        for (i = 0; i < length; i++) {\n          target.setUint8(i, source.getUint8(i));\n        }\n      }\n    } catch (error) {\n      throw new DOMException('ArrayBuffer is detached', DATA_CLONE_ERROR);\n    }\n  }\n\n  mapSet(map, value, clone);\n\n  return clone;\n};\n\nvar cloneView = function (value, type, offset, length, map) {\n  var C = globalThis[type];\n  // in some old engines like Safari 9, typeof C is 'object'\n  // on Uint8ClampedArray or some other constructors\n  if (!isObject(C)) throwUnpolyfillable(type);\n  return new C(cloneBuffer(value.buffer, map), offset, length);\n};\n\nvar structuredCloneInternal = function (value, map) {\n  if (isSymbol(value)) throwUncloneable('Symbol');\n  if (!isObject(value)) return value;\n  // effectively preserves circular references\n  if (map) {\n    if (mapHas(map, value)) return mapGet(map, value);\n  } else map = new Map();\n\n  var type = classof(value);\n  var C, name, cloned, dataTransfer, i, length, keys, key;\n\n  switch (type) {\n    case 'Array':\n      cloned = Array(lengthOfArrayLike(value));\n      break;\n    case 'Object':\n      cloned = {};\n      break;\n    case 'Map':\n      cloned = new Map();\n      break;\n    case 'Set':\n      cloned = new Set();\n      break;\n    case 'RegExp':\n      // in this block because of a Safari 14.1 bug\n      // old FF does not clone regexes passed to the constructor, so get the source and flags directly\n      cloned = new RegExp(value.source, getRegExpFlags(value));\n      break;\n    case 'Error':\n      name = value.name;\n      switch (name) {\n        case 'AggregateError':\n          cloned = new (getBuiltIn(name))([]);\n          break;\n        case 'EvalError':\n        case 'RangeError':\n        case 'ReferenceError':\n        case 'SuppressedError':\n        case 'SyntaxError':\n        case 'TypeError':\n        case 'URIError':\n          cloned = new (getBuiltIn(name))();\n          break;\n        case 'CompileError':\n        case 'LinkError':\n        case 'RuntimeError':\n          cloned = new (getBuiltIn('WebAssembly', name))();\n          break;\n        default:\n          cloned = new Error();\n      }\n      break;\n    case 'DOMException':\n      cloned = new DOMException(value.message, value.name);\n      break;\n    case 'ArrayBuffer':\n    case 'SharedArrayBuffer':\n      cloned = cloneBuffer(value, map, type);\n      break;\n    case 'DataView':\n    case 'Int8Array':\n    case 'Uint8Array':\n    case 'Uint8ClampedArray':\n    case 'Int16Array':\n    case 'Uint16Array':\n    case 'Int32Array':\n    case 'Uint32Array':\n    case 'Float16Array':\n    case 'Float32Array':\n    case 'Float64Array':\n    case 'BigInt64Array':\n    case 'BigUint64Array':\n      length = type === 'DataView' ? value.byteLength : value.length;\n      cloned = cloneView(value, type, value.byteOffset, length, map);\n      break;\n    case 'DOMQuad':\n      try {\n        cloned = new DOMQuad(\n          structuredCloneInternal(value.p1, map),\n          structuredCloneInternal(value.p2, map),\n          structuredCloneInternal(value.p3, map),\n          structuredCloneInternal(value.p4, map)\n        );\n      } catch (error) {\n        cloned = tryNativeRestrictedStructuredClone(value, type);\n      }\n      break;\n    case 'File':\n      if (nativeRestrictedStructuredClone) try {\n        cloned = nativeRestrictedStructuredClone(value);\n        // NodeJS 20.0.0 bug, https://github.com/nodejs/node/issues/47612\n        if (classof(cloned) !== type) cloned = undefined;\n      } catch (error) { /* empty */ }\n      if (!cloned) try {\n        cloned = new File([value], value.name, value);\n      } catch (error) { /* empty */ }\n      if (!cloned) throwUnpolyfillable(type);\n      break;\n    case 'FileList':\n      dataTransfer = createDataTransfer();\n      if (dataTransfer) {\n        for (i = 0, length = lengthOfArrayLike(value); i < length; i++) {\n          dataTransfer.items.add(structuredCloneInternal(value[i], map));\n        }\n        cloned = dataTransfer.files;\n      } else cloned = tryNativeRestrictedStructuredClone(value, type);\n      break;\n    case 'ImageData':\n      // Safari 9 ImageData is a constructor, but typeof ImageData is 'object'\n      try {\n        cloned = new ImageData(\n          structuredCloneInternal(value.data, map),\n          value.width,\n          value.height,\n          { colorSpace: value.colorSpace }\n        );\n      } catch (error) {\n        cloned = tryNativeRestrictedStructuredClone(value, type);\n      } break;\n    default:\n      if (nativeRestrictedStructuredClone) {\n        cloned = nativeRestrictedStructuredClone(value);\n      } else switch (type) {\n        case 'BigInt':\n          // can be a 3rd party polyfill\n          cloned = Object(value.valueOf());\n          break;\n        case 'Boolean':\n          cloned = Object(thisBooleanValue(value));\n          break;\n        case 'Number':\n          cloned = Object(thisNumberValue(value));\n          break;\n        case 'String':\n          cloned = Object(thisStringValue(value));\n          break;\n        case 'Date':\n          cloned = new Date(thisTimeValue(value));\n          break;\n        case 'Blob':\n          try {\n            cloned = value.slice(0, value.size, value.type);\n          } catch (error) {\n            throwUnpolyfillable(type);\n          } break;\n        case 'DOMPoint':\n        case 'DOMPointReadOnly':\n          C = globalThis[type];\n          try {\n            cloned = C.fromPoint\n              ? C.fromPoint(value)\n              : new C(value.x, value.y, value.z, value.w);\n          } catch (error) {\n            throwUnpolyfillable(type);\n          } break;\n        case 'DOMRect':\n        case 'DOMRectReadOnly':\n          C = globalThis[type];\n          try {\n            cloned = C.fromRect\n              ? C.fromRect(value)\n              : new C(value.x, value.y, value.width, value.height);\n          } catch (error) {\n            throwUnpolyfillable(type);\n          } break;\n        case 'DOMMatrix':\n        case 'DOMMatrixReadOnly':\n          C = globalThis[type];\n          try {\n            cloned = C.fromMatrix\n              ? C.fromMatrix(value)\n              : new C(value);\n          } catch (error) {\n            throwUnpolyfillable(type);\n          } break;\n        case 'AudioData':\n        case 'VideoFrame':\n          if (!isCallable(value.clone)) throwUnpolyfillable(type);\n          try {\n            cloned = value.clone();\n          } catch (error) {\n            throwUncloneable(type);\n          } break;\n        case 'CropTarget':\n        case 'CryptoKey':\n        case 'FileSystemDirectoryHandle':\n        case 'FileSystemFileHandle':\n        case 'FileSystemHandle':\n        case 'GPUCompilationInfo':\n        case 'GPUCompilationMessage':\n        case 'ImageBitmap':\n        case 'RTCCertificate':\n        case 'WebAssembly.Module':\n          throwUnpolyfillable(type);\n          // break omitted\n        default:\n          throwUncloneable(type);\n      }\n  }\n\n  mapSet(map, value, cloned);\n\n  switch (type) {\n    case 'Array':\n    case 'Object':\n      keys = objectKeys(value);\n      for (i = 0, length = lengthOfArrayLike(keys); i < length; i++) {\n        key = keys[i];\n        createProperty(cloned, key, structuredCloneInternal(value[key], map));\n      } break;\n    case 'Map':\n      value.forEach(function (v, k) {\n        mapSet(cloned, structuredCloneInternal(k, map), structuredCloneInternal(v, map));\n      });\n      break;\n    case 'Set':\n      value.forEach(function (v) {\n        setAdd(cloned, structuredCloneInternal(v, map));\n      });\n      break;\n    case 'Error':\n      createNonEnumerableProperty(cloned, 'message', structuredCloneInternal(value.message, map));\n      if (hasOwn(value, 'cause')) {\n        createNonEnumerableProperty(cloned, 'cause', structuredCloneInternal(value.cause, map));\n      }\n      if (name === 'AggregateError') {\n        cloned.errors = structuredCloneInternal(value.errors, map);\n      } else if (name === 'SuppressedError') {\n        cloned.error = structuredCloneInternal(value.error, map);\n        cloned.suppressed = structuredCloneInternal(value.suppressed, map);\n      } // break omitted\n    case 'DOMException':\n      if (ERROR_STACK_INSTALLABLE) {\n        createNonEnumerableProperty(cloned, 'stack', structuredCloneInternal(value.stack, map));\n      }\n  }\n\n  return cloned;\n};\n\nvar tryToTransfer = function (rawTransfer, map) {\n  if (!isObject(rawTransfer)) throw new TypeError('Transfer option cannot be converted to a sequence');\n\n  var transfer = [];\n\n  iterate(rawTransfer, function (value) {\n    push(transfer, anObject(value));\n  });\n\n  var i = 0;\n  var length = lengthOfArrayLike(transfer);\n  var buffers = new Set();\n  var value, type, C, transferred, canvas, context;\n\n  while (i < length) {\n    value = transfer[i++];\n    type = classof(value);\n    transferred = undefined;\n\n    if (type === 'ArrayBuffer' ? setHas(buffers, value) : mapHas(map, value)) {\n      throw new DOMException('Duplicate transferable', DATA_CLONE_ERROR);\n    }\n\n    if (type === 'ArrayBuffer') {\n      setAdd(buffers, value);\n      continue;\n    }\n\n    if (PROPER_STRUCTURED_CLONE_TRANSFER) {\n      transferred = nativeStructuredClone(value, { transfer: [value] });\n    } else switch (type) {\n      case 'ImageBitmap':\n        C = globalThis.OffscreenCanvas;\n        if (!isConstructor(C)) throwUnpolyfillable(type, TRANSFERRING);\n        try {\n          canvas = new C(value.width, value.height);\n          context = canvas.getContext('bitmaprenderer');\n          context.transferFromImageBitmap(value);\n          transferred = canvas.transferToImageBitmap();\n        } catch (error) { /* empty */ }\n        break;\n      case 'AudioData':\n      case 'VideoFrame':\n        if (!isCallable(value.clone) || !isCallable(value.close)) throwUnpolyfillable(type, TRANSFERRING);\n        try {\n          transferred = value.clone();\n          value.close();\n        } catch (error) { /* empty */ }\n        break;\n      case 'MediaSourceHandle':\n      case 'MessagePort':\n      case 'MIDIAccess':\n      case 'OffscreenCanvas':\n      case 'ReadableStream':\n      case 'RTCDataChannel':\n      case 'TransformStream':\n      case 'WebTransportReceiveStream':\n      case 'WebTransportSendStream':\n      case 'WritableStream':\n        throwUnpolyfillable(type, TRANSFERRING);\n    }\n\n    if (transferred === undefined) throw new DOMException('This object cannot be transferred: ' + type, DATA_CLONE_ERROR);\n\n    mapSet(map, value, transferred);\n  }\n\n  return buffers;\n};\n\nvar detachBuffers = function (buffers) {\n  setIterate(buffers, function (buffer) {\n    if (PROPER_STRUCTURED_CLONE_TRANSFER) {\n      nativeStructuredClone(buffer, { transfer: [buffer] });\n    } else if (isCallable(buffer.transfer)) {\n      buffer.transfer();\n    } else if (detachTransferable) {\n      detachTransferable(buffer);\n    } else {\n      throwUnpolyfillable('ArrayBuffer', TRANSFERRING);\n    }\n  });\n};\n\n// `structuredClone` method\n// https://html.spec.whatwg.org/multipage/structured-data.html#dom-structuredclone\n$({ global: true, enumerable: true, sham: !PROPER_STRUCTURED_CLONE_TRANSFER, forced: FORCED_REPLACEMENT }, {\n  structuredClone: function structuredClone(value /* , { transfer } */) {\n    var options = validateArgumentsLength(arguments.length, 1) > 1 && !isNullOrUndefined(arguments[1]) ? anObject(arguments[1]) : undefined;\n    var transfer = options ? options.transfer : undefined;\n    var map, buffers;\n\n    if (transfer !== undefined) {\n      map = new Map();\n      buffers = tryToTransfer(transfer, map);\n    }\n\n    var clone = structuredCloneInternal(value, map);\n\n    // since of an issue with cloning views of transferred buffers, we a forced to detach them later\n    // https://github.com/zloirock/core-js/issues/1265\n    if (buffers) detachBuffers(buffers);\n\n    return clone;\n  }\n});\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/modules/web.structured-clone.js?\n}");

/***/ },

/***/ "./node_modules/core-js/stable/structured-clone.js"
/*!*********************************************************!*\
  !*** ./node_modules/core-js/stable/structured-clone.js ***!
  \*********************************************************/
(module, __unused_webpack_exports, __webpack_require__) {

eval("{\n__webpack_require__(/*! ../modules/es.error.to-string */ \"./node_modules/core-js/modules/es.error.to-string.js\");\n__webpack_require__(/*! ../modules/es.array.iterator */ \"./node_modules/core-js/modules/es.array.iterator.js\");\n__webpack_require__(/*! ../modules/es.object.keys */ \"./node_modules/core-js/modules/es.object.keys.js\");\n__webpack_require__(/*! ../modules/es.object.to-string */ \"./node_modules/core-js/modules/es.object.to-string.js\");\n__webpack_require__(/*! ../modules/es.map */ \"./node_modules/core-js/modules/es.map.js\");\n__webpack_require__(/*! ../modules/es.set */ \"./node_modules/core-js/modules/es.set.js\");\n__webpack_require__(/*! ../modules/web.dom-exception.constructor */ \"./node_modules/core-js/modules/web.dom-exception.constructor.js\");\n__webpack_require__(/*! ../modules/web.dom-exception.stack */ \"./node_modules/core-js/modules/web.dom-exception.stack.js\");\n__webpack_require__(/*! ../modules/web.dom-exception.to-string-tag */ \"./node_modules/core-js/modules/web.dom-exception.to-string-tag.js\");\n__webpack_require__(/*! ../modules/web.structured-clone */ \"./node_modules/core-js/modules/web.structured-clone.js\");\nvar path = __webpack_require__(/*! ../internals/path */ \"./node_modules/core-js/internals/path.js\");\n\nmodule.exports = path.structuredClone;\n\n\n//# sourceURL=webpack://@skybrush/live/./node_modules/core-js/stable/structured-clone.js?\n}");

/***/ }

/******/ 	});
/************************************************************************/
/******/ 	// The module cache
/******/ 	const __webpack_module_cache__ = {};
/******/ 	
/******/ 	// The require function
/******/ 	function __webpack_require__(moduleId) {
/******/ 		// Check if module is in cache
/******/ 		const cachedModule = __webpack_module_cache__[moduleId];
/******/ 		if (cachedModule !== undefined) {
/******/ 			return cachedModule.exports;
/******/ 		}
/******/ 		// Create a new module (and put it into the cache)
/******/ 		const module = __webpack_module_cache__[moduleId] = {
/******/ 			// no module.id needed
/******/ 			// no module.loaded needed
/******/ 			exports: {}
/******/ 		};
/******/ 	
/******/ 		// Execute the module function
/******/ 		if (!(moduleId in __webpack_modules__)) {
/******/ 			delete __webpack_module_cache__[moduleId];
/******/ 			const e = new Error("Cannot find module '" + moduleId + "'");
/******/ 			e.code = 'MODULE_NOT_FOUND';
/******/ 			throw e;
/******/ 		}
/******/ 		__webpack_modules__[moduleId].call(module.exports, module, module.exports, __webpack_require__);
/******/ 	
/******/ 		// Return the exports of the module
/******/ 		return module.exports;
/******/ 	}
/******/ 	
/************************************************************************/
/******/ 	/* webpack/runtime/global */
/******/ 	(() => {
/******/ 		__webpack_require__.g = (function() {
/******/ 			if (typeof globalThis === 'object') return globalThis;
/******/ 			try {
/******/ 				return this || new Function('return this')();
/******/ 			} catch (e) {
/******/ 				if (typeof window === 'object') return window;
/******/ 			}
/******/ 		})();
/******/ 	})();
/******/ 	
/************************************************************************/
/******/ 	
/******/ 	// startup
/******/ 	// Load entry module and return exports
/******/ 	// This entry module is referenced by other modules so it can't be inlined
/******/ 	__webpack_require__("./node_modules/core-js/full/set/add-all.js");
/******/ 	__webpack_require__("./node_modules/core-js/full/set/delete-all.js");
/******/ 	let __webpack_exports__ = __webpack_require__("./node_modules/core-js/full/structured-clone.js");
/******/ 	
/******/ })()
;