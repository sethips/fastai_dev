#AUTOGENERATED! DO NOT EDIT! File to edit: dev/01_core.ipynb (unless otherwise specified).

__all__ = ['chk', 'ifnone', 'noop', 'noops', 'range_of', 'is_iter', 'listify', 'tuplify', 'tensor', 'compose',
           'uniqueify', 'setify', 'make_cross_image', 'coll_repr', 'add_docs', 'docs', 'ListContainer', 'mask2idxs',
           'is_listy', 'opt_call']

from .test import *

from .imports import *

from itertools import zip_longest

def chk(f): return typechecked(always=True)(f)

Tensor.ndim = property(lambda x: x.dim())

def ifnone(a, b):
    "`b` if `a` is None else `a`"
    return b if a is None else a

def noop (x, *args, **kwargs):
    "Do nothing"
    return x

def noops(self, x, *args, **kwargs):
    "Do nothing (method)"
    return x

def range_of(x):
    "All indices of collection `x` (i.e. `list(range(len(x)))`)"
    return list(range(len(x)))

def is_iter(o):
    "Test whether `o` can be used in a `for` loop"
    #Rank 0 tensors in PyTorch are not really iterable
    return isinstance(o, (Iterable,Generator)) and getattr(o,'ndim',1)

def listify(o):
    "Make `o` a list."
    if o is None: return []
    if isinstance(o, list): return o
    if isinstance(o, (str,np.ndarray,Tensor)): return [o]
    if is_iter(o): return list(o)
    return [o]

def tuplify(o):
    "Make `o` a tuple"
    return tuple(listify(o))

def tensor(x, *rest):
    "Like `torch.as_tensor`, but handle lists too, and can pass multiple vector elements directly."
    if len(rest): x = tuplify(x)+rest
    # Pytorch bug in dataloader using num_workers>0
    if isinstance(x, (tuple,list)) and len(x)==0: return tensor(0)
    res = torch.tensor(x) if isinstance(x, (tuple,list)) else as_tensor(x)
    if res.dtype is torch.int32:
        warn('Tensor is int32: upgrading to int64; for better performance use int64 input')
        return res.long()
    return res

@chk
def compose(*funcs: Callable):
    "Create a function that composes all functions in `funcs`, passing along remaining `*args` and `**kwargs` to all"
    def _inner(x, *args, **kwargs):
        for f in listify(funcs): x = f(x, *args, **kwargs)
        return x
    return _inner

def uniqueify(x, sort=False, bidir=False, start=None):
    "Return the unique elements in `x`, optionally `sort`-ed, optionally return the reverse correspondance."
    res = list(OrderedDict.fromkeys(x).keys())
    if start is not None: res = listify(start)+res
    if sort: res.sort()
    if bidir: return res, {v:k for k,v in enumerate(res)}
    return res

def setify(o): return o if isinstance(o,set) else set(listify(o))

def make_cross_image(bw=True):
    "Create a tensor containing a cross image, either `bw` (True) or color"
    if bw:
        im = torch.zeros(5,5)
        im[2,:] = 1.
        im[:,2] = 1.
    else:
        im = torch.zeros(3,5,5)
        im[0,2,:] = 1.
        im[1,:,2] = 1.
    return im

def coll_repr(c, max=1000):
    "String repr of up to `max` items of (possibly lazy) collection `c`"
    return f'({len(c)} items) [' + ','.join(itertools.islice(map(str,c), 10)) + ('...'
            if len(c)>10 else '') + ']'

def add_docs(cls, **docs):
    "Copy values from `docs` to `cls` docstrings, and confirm all public methods are documented"
    for k,v in docs.items(): getattr(cls,k).__doc__ = v
    # List of public callables without docstring
    nodoc = [c for n,c in vars(cls).items() if isinstance(c,Callable)
             and not n.startswith('_') and c.__doc__ is None]
    assert not nodoc, f"Missing docs: {nodoc}"
    assert cls.__doc__ is not None, f"Missing class docs: {cls}"

def docs(cls):
    "Decorator version of `add_docs"
    add_docs(cls, **cls._docs)
    return cls

def _mask2idxs(mask):
    mask = list(mask)
    if isinstance(mask[0],bool): return [i for i,m in enumerate(mask) if m]
    return [int(i) for i in mask]

@docs
class ListContainer():
    "Behaves like a list of `items` but can also index with list of indices or masks"
    _xtra =  [o for o in dir(list) if not o.startswith('_')]
    def __getattr__(self,k):
        "Pass on all `list` methods to `items` (e.g. `append`, `sort`, ...)"
        if k in self._xtra: return getattr(self.items, k)
        raise AttributeError(k)

    def __getitem__(self, idx):
        res = [self.items[i] for i in _mask2idxs(idx)] if is_iter(idx) else self.items[idx]
        if is_listy(res) and not isinstance(res,ListContainer): res = ListContainer(res)
        return res

    def __init__(self, items, use_list=False): self.items = list(items) if use_list else listify(items)
    def __len__(self): return len(self.items)
    def __iter__(self): return iter(self.items)
    def __setitem__(self, i, o): self.items[i] = o
    def __delitem__(self, i): del(self.items[i])
    def __repr__(self): return f'{self.__class__.__name__} {coll_repr(self)}'
    def __eq__(self,b): return all_equal(b,self)
    def __dir__(self): return custom_dir(self, self._xtra)

    def mapped(self, f):    return ListContainer(map(f, self))
    def zipped(self):       return ListContainer(zip(*self))
    def itemgot(self, idx): return self.mapped(itemgetter(idx))
    def attrgot(self, k):   return self.mapped(attrgetter(k))

    _docs=dict(mapped="Create new `ListContainer` with `f` applied to all `items`",
              zipped="Create new `ListContainer` with `zip(*items)`",
              itemgot="Create new `ListContainer` with item `idx` of all `items`",
              attrgot="Create new `ListContainer` with attr `k` of all `items`")

def mask2idxs(mask):
    "Convert bool mask or index list to index `ListContainer`"
    return ListContainer(_mask2idxs(mask))

def is_listy(x):
    "`isinstance(x, (tuple,list,ListContainer))`"
    return isinstance(x, (tuple,list,ListContainer))

#Comes from 02_data_pipeline.ipynb.
def opt_call(f, fname='__call__', *args, **kwargs):
    "Call `f.{fname}(*args, **kwargs)`, or `noop` if not defined"
    return getattr(f,fname,noop)(*args, **kwargs)